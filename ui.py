"""Elementos de interfaz compartidos por todas las páginas."""
from __future__ import annotations

import streamlit as st

from core import config, estilos
from core.mqtt_client import PuenteMQTT, obtener_puente


@st.fragment(run_every=3)
def _estado_conexion(puente: PuenteMQTT):
    s = puente.snapshot()
    broker = '<span class="punto on"></span> Broker MQTT conectado' if s.broker_ok else '<span class="punto mal"></span> Broker MQTT sin conexión'
    if s.en_vivo:
        inv = '<span class="punto on"></span> Invernadero enviando datos'
    elif s.dispositivo == "offline":
        inv = '<span class="punto mal"></span> Invernadero desconectado'
    else:
        inv = '<span class="punto espera"></span> Esperando al invernadero'
    st.markdown(f'<div style="line-height:2;font-size:.92rem">{broker}<br>{inv}</div>', unsafe_allow_html=True)


def iniciar_pagina(titulo: str, icono: str = ":material/eco:") -> PuenteMQTT:
    """Configura la página, dibuja la barra lateral y devuelve el puente MQTT."""
    estilos.aplicar()

    # El valor "oficial" vive en session_state["base"] para sobrevivir al cambio de página.
    if "base_w" not in st.session_state:
        st.session_state["base_w"] = config.base_topic()
    if "api_w" not in st.session_state:
        st.session_state["api_w"] = st.session_state.get("api_key", "")

    with st.sidebar:
        st.markdown(
            '<div class="inv-marca">Invernadero<span>Control y monitoreo con ESP32</span></div>',
            unsafe_allow_html=True,
        )
        st.text_input(
            "Topic base MQTT",
            key="base_w",
            help="Debe ser idéntico al TOPIC_BASE del sketch de Wokwi.",
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
        st.divider()
        _estado_conexion(puente)
    return puente
