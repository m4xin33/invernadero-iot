/*
 * Invernadero inteligente - ESP32 (simulado en Wokwi)
 *
 * Sensores : DHT22 (temperatura/humedad aire), potenciómetro (humedad de suelo),
 *            LDR (luz)
 * Actuadores: LED azul (bomba de riego), LED amarillo (lámpara de crecimiento),
 *            servo (ventana de ventilación)
 * Comunicación: MQTT (PubSubClient) <-> Streamlit
 *
 * Topics (TOPIC_BASE + sufijo):
 *   /sensores  (ESP32 -> app)  JSON con lecturas y estado de actuadores
 *   /comandos  (app -> ESP32)  JSON con órdenes, p. ej. {"bomba":true}
 *   /estado    (ESP32 -> app)  "online" / "offline" (retenido, con LWT)
 *
 * IMPORTANTE: cambia TOPIC_BASE por un identificador propio y usa el mismo
 * valor en la app de Streamlit (barra lateral o secrets).
 */
#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <ESP32Servo.h>
#include <ArduinoJson.h>

// ------------------------- CONFIGURACIÓN -------------------------
const char* WIFI_SSID = "Wokwi-GUEST";
const char* WIFI_PASS = "";
const char* MQTT_HOST = "broker.hivemq.com";
const uint16_t MQTT_PORT = 1883;
const char* TOPIC_BASE = "eafit/invernadero/inv-7k7a86o0";

// Pines
const int PIN_DHT     = 15;
const int PIN_SUELO   = 34;  // potenciómetro (ADC1)
const int PIN_LDR     = 35;  // salida analógica del módulo LDR (ADC1)
const int PIN_BOMBA   = 26;
const int PIN_LAMPARA = 27;
const int PIN_SERVO   = 13;

// En el módulo LDR de Wokwi la salida analógica sube cuando hay MENOS luz.
// Si en tu simulación ves el comportamiento contrario, pon false.
const bool LDR_INVERTIDO = true;

const unsigned long INTERVALO_PUBLICACION_MS = 2000;
const unsigned long BOMBA_MAX_MS = 60000;  // seguridad en modo manual
const int HISTERESIS = 10;                 // puntos porcentuales

// ------------------------- OBJETOS Y ESTADO -------------------------
DHT dht(PIN_DHT, DHT22);
Servo ventanaServo;
WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);

String topicSensores, topicComandos, topicEstado;

struct Estado {
  bool modoAuto = true;
  bool bomba = false;
  bool lampara = false;
  int ventana = 0;          // 0..100 %
  int umbralSuelo = 35;     // % mínimo de humedad de suelo
  int umbralLuz = 30;       // % mínimo de luz
  float umbralTemp = 28.0;  // °C máxima antes de abrir la ventana
} est;

float temp = NAN, hum = NAN;
int suelo = 0, luz = 0;
unsigned long ultimaPub = 0, bombaDesde = 0;

// ------------------------- SALIDAS -------------------------
void ponerBomba(bool encendida) {
  if (encendida && !est.bomba) bombaDesde = millis();
  est.bomba = encendida;
}

void aplicarSalidas() {
  digitalWrite(PIN_BOMBA, est.bomba ? HIGH : LOW);
  digitalWrite(PIN_LAMPARA, est.lampara ? HIGH : LOW);
  ventanaServo.write(map(est.ventana, 0, 100, 0, 90));
}

// ------------------------- SENSORES -------------------------
void leerSensores() {
  float t = dht.readTemperature();
  float h = dht.readHumidity();
  if (!isnan(t)) temp = t;
  if (!isnan(h)) hum = h;

  suelo = constrain(map(analogRead(PIN_SUELO), 0, 4095, 0, 100), 0, 100);
  int l = constrain(map(analogRead(PIN_LDR), 0, 4095, 0, 100), 0, 100);
  luz = LDR_INVERTIDO ? 100 - l : l;
}

// ------------------------- LÓGICA AUTOMÁTICA -------------------------
void logicaAutomatica() {
  if (!est.modoAuto) return;

  if (suelo < est.umbralSuelo) ponerBomba(true);
  else if (suelo > est.umbralSuelo + HISTERESIS) ponerBomba(false);

  if (luz < est.umbralLuz) est.lampara = true;
  else if (luz > est.umbralLuz + HISTERESIS) est.lampara = false;

  if (!isnan(temp)) {
    if (temp > est.umbralTemp) est.ventana = 100;
    else if (temp < est.umbralTemp - 2.0) est.ventana = 0;
  }
}

// Seguridad: en modo manual la bomba no puede quedar encendida indefinidamente.
void seguridadBomba() {
  if (!est.modoAuto && est.bomba && millis() - bombaDesde > BOMBA_MAX_MS) {
    est.bomba = false;
    Serial.println("[SEGURIDAD] Bomba apagada por tiempo maximo en modo manual");
  }
}

// ------------------------- MQTT -------------------------
void publicarSensores() {
  JsonDocument doc;
  if (!isnan(temp)) doc["temp"] = roundf(temp * 10) / 10.0f;
  if (!isnan(hum)) doc["hum"] = roundf(hum * 10) / 10.0f;
  doc["suelo"] = suelo;
  doc["luz"] = luz;
  doc["bomba"] = est.bomba;
  doc["lampara"] = est.lampara;
  doc["ventana"] = est.ventana;
  doc["modo"] = est.modoAuto ? "auto" : "manual";
  JsonObject u = doc["umbrales"].to<JsonObject>();
  u["suelo"] = est.umbralSuelo;
  u["luz"] = est.umbralLuz;
  u["temp"] = est.umbralTemp;
  doc["uptime"] = millis() / 1000;

  char buf[384];
  size_t n = serializeJson(doc, buf, sizeof(buf));
  mqtt.publish(topicSensores.c_str(), (const uint8_t*)buf, n, false);
}

void onMensaje(char* topic, byte* payload, unsigned int length) {
  JsonDocument doc;
  DeserializationError err = deserializeJson(doc, payload, length);
  if (err) {
    Serial.print("[MQTT] JSON invalido: ");
    Serial.println(err.c_str());
    return;
  }

  bool tocaActuador = false;
  bool traeModo = doc["modo"].is<const char*>();

  if (traeModo) est.modoAuto = (strcmp(doc["modo"], "auto") == 0);
  if (doc["bomba"].is<bool>()) { ponerBomba(doc["bomba"].as<bool>()); tocaActuador = true; }
  if (doc["lampara"].is<bool>()) { est.lampara = doc["lampara"].as<bool>(); tocaActuador = true; }
  if (doc["ventana"].is<int>()) { est.ventana = constrain(doc["ventana"].as<int>(), 0, 100); tocaActuador = true; }

  if (doc["umbral_suelo"].is<int>()) est.umbralSuelo = constrain(doc["umbral_suelo"].as<int>(), 0, 100);
  if (doc["umbral_luz"].is<int>()) est.umbralLuz = constrain(doc["umbral_luz"].as<int>(), 0, 100);
  if (doc["umbral_temp"].is<float>()) est.umbralTemp = constrain(doc["umbral_temp"].as<float>(), 0.0f, 60.0f);

  // Una orden manual sobre un actuador saca al sistema del modo automático.
  if (tocaActuador && !traeModo) est.modoAuto = false;

  Serial.printf("[MQTT] Comando recibido en %s\n", topic);
  aplicarSalidas();
  publicarSensores();  // confirmación inmediata hacia la app
}

void conectarWiFi() {
  Serial.print("Conectando a WiFi");
  WiFi.begin(WIFI_SSID, WIFI_PASS, 6);
  while (WiFi.status() != WL_CONNECTED) {
    delay(250);
    Serial.print(".");
  }
  Serial.println(" OK");
}

void conectarMQTT() {
  while (!mqtt.connected()) {
    Serial.print("Conectando a MQTT...");
    String cid = "esp32-inv-" + String((uint32_t)esp_random(), HEX);
    // Last Will: si el ESP32 se cae, el broker publica "offline" (retenido)
    if (mqtt.connect(cid.c_str(), nullptr, nullptr, topicEstado.c_str(), 0, true, "offline")) {
      Serial.println(" OK");
      mqtt.subscribe(topicComandos.c_str());
      mqtt.publish(topicEstado.c_str(), "online", true);
    } else {
      Serial.printf(" fallo (rc=%d), reintento en 2 s\n", mqtt.state());
      delay(2000);
    }
  }
}

// ------------------------- SETUP / LOOP -------------------------
void setup() {
  Serial.begin(115200);
  pinMode(PIN_BOMBA, OUTPUT);
  pinMode(PIN_LAMPARA, OUTPUT);
  dht.begin();
  ventanaServo.setPeriodHertz(50);
  ventanaServo.attach(PIN_SERVO, 500, 2400);
  aplicarSalidas();

  topicSensores = String(TOPIC_BASE) + "/sensores";
  topicComandos = String(TOPIC_BASE) + "/comandos";
  topicEstado = String(TOPIC_BASE) + "/estado";

  conectarWiFi();
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setCallback(onMensaje);
  mqtt.setBufferSize(512);
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) conectarWiFi();
  if (!mqtt.connected()) conectarMQTT();
  mqtt.loop();

  unsigned long ahora = millis();
  if (ahora - ultimaPub >= INTERVALO_PUBLICACION_MS) {
    ultimaPub = ahora;
    leerSensores();
    logicaAutomatica();
    seguridadBomba();
    aplicarSalidas();
    publicarSensores();
  }
}
