"""Simulador del ESP32 en Python (mismo protocolo MQTT que el sketch de Wokwi).

Sirve para desarrollar y probar la app de Streamlit sin abrir Wokwi, o como
plan B si falla el internet del simulador durante la sustentación.

Uso:
    python tools/simulador_esp32.py --base eafit/invernadero/mi_id
    python tools/simulador_esp32.py --base mi/topic --host localhost --port 1883
"""
from __future__ import annotations

import argparse
import json
import random
import time

import paho.mqtt.client as mqtt


class Invernadero:
    def __init__(self):
        self.auto = True
        self.bomba = False
        self.lampara = False
        self.ventana = 0
        self.u_suelo, self.u_luz, self.u_temp = 35, 30, 28.0
        self.temp, self.hum = 24.0, 60.0
        self.suelo, self.luz = 55.0, 70.0

    def paso(self):
        # El suelo se seca solo; la bomba lo humedece. La ventana enfría.
        self.suelo = max(0.0, min(100.0, self.suelo + (4.0 if self.bomba else -0.6)))
        self.temp += random.uniform(-0.2, 0.3) - (0.4 if self.ventana > 50 else 0.0)
        self.temp = max(12.0, min(40.0, self.temp))
        self.hum = max(30.0, min(95.0, self.hum + random.uniform(-1, 1)))
        self.luz = max(0.0, min(100.0, self.luz + random.uniform(-3, 3) + (6 if self.lampara else 0)))
        if self.auto:
            if self.suelo < self.u_suelo:
                self.bomba = True
            elif self.suelo > self.u_suelo + 10:
                self.bomba = False
            if self.luz < self.u_luz:
                self.lampara = True
            elif self.luz > self.u_luz + 10:
                self.lampara = False
            if self.temp > self.u_temp:
                self.ventana = 100
            elif self.temp < self.u_temp - 2:
                self.ventana = 0

    def comando(self, d: dict):
        modo = d.get("modo")
        if modo in ("auto", "manual"):
            self.auto = modo == "auto"
        toca = False
        if isinstance(d.get("bomba"), bool):
            self.bomba, toca = d["bomba"], True
        if isinstance(d.get("lampara"), bool):
            self.lampara, toca = d["lampara"], True
        if isinstance(d.get("ventana"), int) and not isinstance(d.get("ventana"), bool):
            self.ventana, toca = max(0, min(100, d["ventana"])), True
        if isinstance(d.get("umbral_suelo"), int):
            self.u_suelo = d["umbral_suelo"]
        if isinstance(d.get("umbral_luz"), int):
            self.u_luz = d["umbral_luz"]
        if isinstance(d.get("umbral_temp"), (int, float)):
            self.u_temp = float(d["umbral_temp"])
        if toca and modo is None:
            self.auto = False

    def lectura(self) -> dict:
        return {
            "temp": round(self.temp, 1),
            "hum": round(self.hum, 1),
            "suelo": int(self.suelo),
            "luz": int(self.luz),
            "bomba": self.bomba,
            "lampara": self.lampara,
            "ventana": self.ventana,
            "modo": "auto" if self.auto else "manual",
            "umbrales": {"suelo": self.u_suelo, "luz": self.u_luz, "temp": self.u_temp},
            "uptime": int(time.time() - INICIO),
        }


INICIO = time.time()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", required=True, help="topic base (el mismo de la app)")
    ap.add_argument("--host", default="broker.hivemq.com")
    ap.add_argument("--port", type=int, default=1883)
    ap.add_argument("--intervalo", type=float, default=2.0)
    a = ap.parse_args()

    base = a.base.strip("/")
    t_sens, t_cmd, t_est = f"{base}/sensores", f"{base}/comandos", f"{base}/estado"
    inv = Invernadero()

    cli = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"sim-esp32-{random.randint(0, 9999)}")
    cli.will_set(t_est, "offline", retain=True)

    def on_connect(c, u, f, rc, p=None):
        c.subscribe(t_cmd)
        c.publish(t_est, "online", retain=True)
        print(f"Conectado a {a.host}:{a.port} · base={base}")

    def on_message(c, u, msg):
        try:
            d = json.loads(msg.payload)
            print("Comando:", d)
            inv.comando(d)
            c.publish(t_sens, json.dumps(inv.lectura()))
        except Exception as exc:
            print("Comando inválido:", exc)

    cli.on_connect, cli.on_message = on_connect, on_message
    cli.connect(a.host, a.port, keepalive=30)
    cli.loop_start()
    try:
        while True:
            inv.paso()
            cli.publish(t_sens, json.dumps(inv.lectura()))
            time.sleep(a.intervalo)
    except KeyboardInterrupt:
        cli.publish(t_est, "offline", retain=True)
        cli.loop_stop()
        cli.disconnect()


if __name__ == "__main__":
    main()
