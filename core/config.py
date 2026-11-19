"""Configuración central: broker MQTT, topic base y claves opcionales.

Orden de prioridad: barra lateral (session_state) > st.secrets > variables de
entorno > valores por defecto.
"""
from __future__ import annotations

import os

import streamlit as st

BROKER_POR_DEFECTO = "broker.hivemq.com"
PUERTO_POR_DEFECTO = 1883
BASE_POR_DEFECTO = "eafit/invernadero/inv-7k7a86o0"

# Sufijos de topics (deben coincidir con el firmware de Wokwi)
SUFIJO_SENSORES = "sensores"
SUFIJO_COMANDOS = "comandos"
SUFIJO_ESTADO = "estado"

# Un dato se considera "en vivo" si llegó hace menos de estos segundos
SEGUNDOS_DATO_VIVO = 8

ZONA_HORARIA = "America/Bogota"


def _secreto(nombre: str, defecto=None):
    try:
        if nombre in st.secrets:
            return st.secrets[nombre]
    except Exception:  # no hay secrets.toml
        pass
    return os.environ.get(nombre, defecto)


def broker() -> str:
    return str(_secreto("MQTT_HOST", BROKER_POR_DEFECTO))


def puerto() -> int:
    return int(_secreto("MQTT_PORT", PUERTO_POR_DEFECTO))


def base_topic() -> str:
    return st.session_state.get("base") or str(_secreto("MQTT_BASE", BASE_POR_DEFECTO))


def api_key_anthropic() -> str | None:
    return st.session_state.get("api_key") or _secreto("ANTHROPIC_API_KEY")
