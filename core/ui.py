"""Elementos de interfaz compartidos por todas las páginas."""
from __future__ import annotations

import streamlit as st

from core import config
from core.mqtt_client import PuenteMQTT, obtener_puente


@st.fragment(run_every=3)
def _estado_conexion(puente: PuenteMQTT):
    s = puente.snapshot()
    st.caption("Broker MQTT: " + ("🟢 conectado" if s.broker_ok else "🔴 sin conexión"))
    if s.en_vivo:
        st.caption("Invernadero (Wokwi): 🟢 enviando datos")
    elif s.dispositivo == "offline":
        st.caption("Invernadero (Wokwi): 🔴 desconectado")
    else:
        st.caption("Invernadero (Wokwi): 🟡 esperando datos…")


def iniciar_pagina(titulo: str, icono: str) -> PuenteMQTT:
    """Configura la página, dibuja la barra lateral y devuelve el puente MQTT."""
    st.set_page_config(page_title=f"{titulo} · Invernadero IoT", page_icon=icono, layout="wide")

    # El valor "oficial" vive en session_state["base"] para sobrevivir al cambio de página.
    if "base_w" not in st.session_state:
        st.session_state["base_w"] = config.base_topic()
    if "api_w" not in st.session_state:
        st.session_state["api_w"] = st.session_state.get("api_key", "")

    with st.sidebar:
        st.header("🌱 Invernadero IoT")
        st.text_input(
            "Topic base MQTT",
            key="base_w",
            help="Debe ser idéntico al TOPIC_BASE del sketch de Wokwi. Usa un valor único tuyo.",
        )
        st.session_state["base"] = st.session_state["base_w"].strip()
        with st.expander("Opciones avanzadas"):
            st.text_input(
                "API key de Anthropic (opcional)",
                key="api_w",
                type="password",
                help="Solo para la segunda opinión con Claude en el diagnóstico por imagen. No se guarda.",
            )
            st.session_state["api_key"] = st.session_state["api_w"].strip()
            st.caption(f"Broker: `{config.broker()}:{config.puerto()}`")

    puente = obtener_puente()
    with st.sidebar:
        _estado_conexion(puente)
    return puente
