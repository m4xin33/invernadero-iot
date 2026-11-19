import hashlib

import pandas as pd
import streamlit as st

from core import estilos
from core.comandos import interpretar
from core.ui import iniciar_pagina
from core.voz import transcribir

puente = iniciar_pagina("Control")

st.title("Control")
estilos.lead("Da órdenes al invernadero con botones, texto o voz. Cada orden manual pasa el sistema a modo manual.")


def enviar(payload: dict, origen: str):
    if puente.publicar_comando(payload, origen):
        st.toast(f"Orden enviada: {payload}", icon=":material/send:")
    else:
        st.toast("No hay conexión con el broker MQTT", icon=":material/warning:")


# ------------------------------------------------------------------ estado
@st.fragment(run_every=2)
def panel_estado():
    s = puente.snapshot()
    if not s.en_vivo:
        st.warning("Sin datos recientes. Inicia la simulación en Wokwi y revisa que el topic base sea el mismo.")
    st.markdown(estilos.estado_actuadores(s.ultimo, s.edad), unsafe_allow_html=True)


panel_estado()

# ------------------------------------------------------------------ botones y slider
estilos.seccion("Botones y slider")
colb, coll, colv = st.columns(3, gap="large")
with colb:
    estilos.subtitulo("Bomba de riego")
    b1, b2 = st.columns(2)
    if b1.button("Encender", key="bomba_on", use_container_width=True):
        enviar({"bomba": True}, "botón")
    if b2.button("Apagar", key="bomba_off", use_container_width=True):
        enviar({"bomba": False}, "botón")
with coll:
    estilos.subtitulo("Lámpara de crecimiento")
    l1, l2 = st.columns(2)
    if l1.button("Encender", key="lampara_on", use_container_width=True):
        enviar({"lampara": True}, "botón")
    if l2.button("Apagar", key="lampara_off", use_container_width=True):
        enviar({"lampara": False}, "botón")
with colv:
    estilos.subtitulo("Ventana")
    st.slider(
        "Apertura (%)",
        0,
        100,
        0,
        5,
        key="slider_ventana",
        on_change=lambda: enviar({"ventana": int(st.session_state["slider_ventana"])}, "slider"),
    )

st.write("")
m1, m2, _ = st.columns([1.5, 1.5, 3])
if m1.button("Modo automático", key="modo_auto", icon=":material/autorenew:", use_container_width=True):
    enviar({"modo": "auto"}, "botón")
if m2.button("Modo manual", key="modo_manual", icon=":material/pan_tool:", use_container_width=True):
    enviar({"modo": "manual"}, "botón")


# ------------------------------------------------------------------ texto y voz
def procesar_orden(texto: str, origen: str) -> dict:
    r = interpretar(texto)
    if r.ok:
        enviar(r.payload, origen)
    return {"texto": texto, "entendido": r.entendido, "errores": r.errores, "payload": r.payload}


def mostrar_feedback(clave: str):
    fb = st.session_state.get(clave)
    if not fb:
        return
    if fb.get("texto"):
        st.write(f"Escuché: «{fb['texto']}»")
    for e in fb.get("errores", []):
        st.warning(e)
    if fb.get("entendido"):
        st.success("Entendí: " + " · ".join(fb["entendido"]))
        st.code(fb["payload"], language="json")


estilos.seccion("Texto y voz", "Habla o escribe como lo harías con una persona: «enciende la bomba», «abre la ventana al 50 por ciento», «apaga la luz y riega las plantas».")
ctexto, cvoz = st.columns(2, gap="large")

with ctexto:
    estilos.subtitulo("Escribir una orden")
    with st.form("form_texto", clear_on_submit=True):
        texto = st.text_input("Orden", placeholder="enciende la lámpara", label_visibility="collapsed")
        if st.form_submit_button("Enviar orden", icon=":material/send:"):
            if texto.strip():
                st.session_state["fb_texto"] = procesar_orden(texto, "texto")
    mostrar_feedback("fb_texto")

with cvoz:
    estilos.subtitulo("Decir una orden")
    audio = st.audio_input("Graba tu orden", key="audio_orden", label_visibility="collapsed")
    if audio is not None:
        huella = hashlib.md5(audio.getvalue()).hexdigest()
        if st.session_state.get("huella_audio") != huella:
            st.session_state["huella_audio"] = huella
            with st.spinner("Transcribiendo…"):
                texto_voz, error = transcribir(audio.getvalue())
            if texto_voz:
                st.session_state["fb_voz"] = procesar_orden(texto_voz, "voz")
            else:
                st.session_state["fb_voz"] = {"texto": None, "errores": [error], "entendido": [], "payload": {}}
    mostrar_feedback("fb_voz")


# ------------------------------------------------------------------ bitácora
@st.fragment(run_every=3)
def bitacora():
    with st.expander("Órdenes enviadas"):
        filas = puente.snapshot().bitacora
        if filas:
            st.dataframe(pd.DataFrame(filas), hide_index=True)
        else:
            st.caption("Aún no has enviado órdenes.")


st.write("")
bitacora()
