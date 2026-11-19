# 🌱 Invernadero inteligente multimodal

Proyecto final – Interfaces Multimodales. Aplicación **Streamlit** (Python 3.11) que controla y monitorea
un invernadero simulado en **Wokwi** (ESP32) con comunicación **bidireccional por MQTT**.

## Arquitectura

```
┌────────────────────┐   /sensores (JSON)   ┌──────────────────┐   /sensores    ┌─────────────────────┐
│  ESP32 en Wokwi    │ ───────────────────► │   Broker MQTT    │ ─────────────► │  App Streamlit      │
│  DHT22 · suelo     │                      │ (HiveMQ público) │                │  1_Control          │
│  LDR · bomba       │ ◄─────────────────── │                  │ ◄───────────── │  2_Monitoreo_y_diag │
│  lámpara · servo   │   /comandos (JSON)   └──────────────────┘   /comandos    └─────────────────────┘
└────────────────────┘          /estado (online/offline, retenido, LWT)
```

### Topics MQTT (`<BASE>` = `eafit/invernadero/<tu_id>`)

| Topic | Sentido | Contenido |
|---|---|---|
| `<BASE>/sensores` | ESP32 → app | `{"temp":24.5,"hum":60,"suelo":47,"luz":72,"bomba":false,"lampara":false,"ventana":0,"modo":"auto","umbrales":{"suelo":35,"luz":30,"temp":28.0},"uptime":123}` cada 2 s y tras cada comando |
| `<BASE>/comandos` | app → ESP32 | `{"bomba":true}`, `{"lampara":false}`, `{"ventana":50}`, `{"modo":"auto"}`, `{"umbral_suelo":40,"umbral_luz":25,"umbral_temp":30.0}` |
| `<BASE>/estado` | ESP32 → app | `online` / `offline` (mensaje retenido + Last Will) |

Regla de diseño: una orden manual sobre un actuador pone el sistema en **modo manual**; `{"modo":"auto"}` devuelve el control a las reglas con histéresis. En modo manual la bomba tiene un **corte de seguridad de 60 s**.

## Los dos ambientes y sus modalidades

| Página | Usuario | Modalidades |
|---|---|---|
| `pages/1_Control.py` | Operador | Botones, slider, **texto** en español, **voz** (`st.audio_input` + reconocimiento de voz) |
| `pages/2_Monitoreo_y_diagnostico.py` | Agrónomo | Gráficas en vivo, sliders de umbrales, **imagen** (cámara o foto) con análisis local + segunda opinión opcional con Claude |

Ejemplos de órdenes de texto/voz: «enciende la bomba», «abre la ventana al 50 por ciento», «apaga la luz y riega las plantas», «modo automático», «apaga todo».

## Estructura

```
app.py                      # Inicio: arquitectura y guía de prueba
pages/                      # Las dos páginas (ambientes)
core/
  mqtt_client.py            # Puente MQTT (hilo propio + estado con lock)
  comandos.py               # Intérprete de órdenes en español (función pura)
  diagnostico.py            # Reglas del semáforo (función pura)
  vision.py                 # Índice de salud por color + Claude opcional
  voz.py                    # Transcripción de voz
  ui.py / config.py         # Barra lateral y configuración
wokwi/                      # sketch.ino, diagram.json, libraries.txt
tools/simulador_esp32.py    # ESP32 simulado en Python (plan B / desarrollo)
tests/                      # pytest (comandos, reglas, visión, páginas)
docs/                       # Esqueleto del informe y guía de sustentación
```

## Cómo ejecutarlo

### 1. Wokwi
1. En [wokwi.com](https://wokwi.com) crea un proyecto **ESP32** y pega `wokwi/sketch.ino`, `wokwi/diagram.json` y `wokwi/libraries.txt`.
2. En `sketch.ino` cambia `TOPIC_BASE` por **tu propio identificador** (el broker de HiveMQ es público y compartido).
3. Pulsa ▶ y espera `Conectando a MQTT... OK` en el monitor serie.

### 2. App en local
```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```
En la barra lateral escribe el mismo **Topic base MQTT**. Debe aparecer *Invernadero (Wokwi): 🟢*.

### 3. Sin Wokwi (desarrollo o plan B)
```bash
python tools/simulador_esp32.py --base eafit/invernadero/<tu_id>
```

### 4. Despliegue en Streamlit Community Cloud
Sube el repositorio a GitHub → *New app* → archivo principal `app.py` → **Advanced settings → Python 3.11**. En *Secrets* pega el contenido de `.streamlit/secrets.toml.example` (`MQTT_BASE`, y opcionalmente `ANTHROPIC_API_KEY`).

### 5. Pruebas
```bash
pip install -r requirements-dev.txt
pytest -q
```

## Mapa a la rúbrica

| Ítem | Dónde se cubre |
|---|---|
| A1 Simulación Wokwi | `wokwi/` (ESP32 + DHT22 + potenciómetro + LDR + 2 LEDs + servo) |
| A2 Comunicación bidireccional | `/sensores` (Wokwi→app) y `/comandos` (app→Wokwi), confirmación inmediata y LWT |
| A3 App multipágina, 2 ambientes | `pages/1_Control.py` y `pages/2_Monitoreo_y_diagnostico.py` |
| A4 Modalidades | Botones, slider, texto, voz, imagen, gráficas |
| A5 Calidad del código | Módulos `core/`, funciones puras con pruebas, `requirements.txt`, README |
| B1 Usabilidad | Estado en vivo, mensajes de retroalimentación, bitácora, semáforo |
| B2 Innovación | Voz en español + diagnóstico por imagen cruzado con el sensor de suelo + IA opcional |

Guías para las demás secciones: [`docs/INFORME_ESQUELETO.md`](docs/INFORME_ESQUELETO.md) (D1–D10) y [`docs/SUSTENTACION.md`](docs/SUSTENTACION.md) (C1–C3).

## Problemas frecuentes

- **No llegan datos:** el topic base de Wokwi y de la app deben ser idénticos; verifica que Wokwi muestre `MQTT ... OK`.
- **El micrófono/cámara no funcionan:** requieren HTTPS o `localhost`, y permiso del navegador.
- **La luz sube cuando oscurezco el LDR:** en `sketch.ino` cambia `LDR_INVERTIDO` a `false`.
- **El reconocimiento de voz falla:** usa el servicio web gratuito de Google; necesita internet. Siempre queda el campo de texto.
