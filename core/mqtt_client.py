"""Puente MQTT <-> Streamlit.

Streamlit re-ejecuta el script en cada interacción, así que el cliente MQTT vive
en un recurso cacheado (``st.cache_resource``) con un hilo propio. Los mensajes
entrantes se guardan en un ``Estado`` protegido por un lock y las páginas lo leen
con ``snapshot()``.
"""
from __future__ import annotations

import json
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field

import paho.mqtt.client as mqtt
import streamlit as st

from core import config


@dataclass
class Instantanea:
    """Copia inmutable del estado, segura para usar en las páginas."""

    ultimo: dict
    ultimo_ts: float
    historial: list
    broker_ok: bool
    dispositivo: str
    bitacora: list

    @property
    def edad(self) -> float | None:
        return None if not self.ultimo_ts else time.time() - self.ultimo_ts

    @property
    def en_vivo(self) -> bool:
        return self.edad is not None and self.edad < config.SEGUNDOS_DATO_VIVO


@dataclass
class _Estado:
    lock: threading.Lock = field(default_factory=threading.Lock)
    ultimo: dict = field(default_factory=dict)
    ultimo_ts: float = 0.0
    historial: deque = field(default_factory=lambda: deque(maxlen=900))
    broker_ok: bool = False
    dispositivo: str = "desconocido"
    bitacora: deque = field(default_factory=lambda: deque(maxlen=60))


class PuenteMQTT:
    def __init__(self, host: str, port: int, base: str):
        self.host, self.port = host, port
        self.base = base.strip("/")
        self.t_sensores = f"{self.base}/{config.SUFIJO_SENSORES}"
        self.t_comandos = f"{self.base}/{config.SUFIJO_COMANDOS}"
        self.t_estado = f"{self.base}/{config.SUFIJO_ESTADO}"
        self._e = _Estado()

        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"streamlit-inv-{uuid.uuid4().hex[:8]}",
        )
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.reconnect_delay_set(min_delay=1, max_delay=10)
        self.client.connect_async(host, port, keepalive=30)
        self.client.loop_start()

    # ---- callbacks (hilo de paho) ----
    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        ok = not reason_code.is_failure
        with self._e.lock:
            self._e.broker_ok = ok
        if ok:
            client.subscribe([(self.t_sensores, 0), (self.t_estado, 0)])

    def _on_disconnect(self, client, userdata, flags, reason_code, properties=None):
        with self._e.lock:
            self._e.broker_ok = False

    def _on_message(self, client, userdata, msg):
        try:
            texto = msg.payload.decode("utf-8", errors="replace")
        except Exception:
            return
        if msg.topic == self.t_estado:
            with self._e.lock:
                self._e.dispositivo = texto.strip()
            return
        if msg.topic == self.t_sensores:
            try:
                datos = json.loads(texto)
            except json.JSONDecodeError:
                return
            if not isinstance(datos, dict):
                return
            ahora = time.time()
            with self._e.lock:
                self._e.ultimo = datos
                self._e.ultimo_ts = ahora
                self._e.dispositivo = "online"
                fila = {k: v for k, v in datos.items() if isinstance(v, (int, float, bool))}
                fila["ts"] = ahora
                self._e.historial.append(fila)

    # ---- API pública ----
    def publicar_comando(self, payload: dict, origen: str = "botón") -> bool:
        enviado = bool(self.client.is_connected())
        if enviado:
            self.client.publish(self.t_comandos, json.dumps(payload), qos=0)
        with self._e.lock:
            self._e.bitacora.appendleft(
                {
                    "hora": time.strftime("%H:%M:%S"),
                    "origen": origen,
                    "comando": json.dumps(payload, ensure_ascii=False),
                    "enviado": enviado,
                }
            )
        return enviado

    def snapshot(self) -> Instantanea:
        with self._e.lock:
            return Instantanea(
                ultimo=dict(self._e.ultimo),
                ultimo_ts=self._e.ultimo_ts,
                historial=list(self._e.historial),
                broker_ok=self._e.broker_ok,
                dispositivo=self._e.dispositivo,
                bitacora=list(self._e.bitacora),
            )

    def cerrar(self):
        self.client.loop_stop()
        self.client.disconnect()


@st.cache_resource(show_spinner=False)
def _crear_puente(host: str, port: int, base: str) -> PuenteMQTT:
    return PuenteMQTT(host, port, base)


def obtener_puente() -> PuenteMQTT:
    return _crear_puente(config.broker(), config.puerto(), config.base_topic())
