import hashlib

import pandas as pd
import streamlit as st

from core.comandos import interpretar
from core.ui import iniciar_pagina
from core.voz import transcribir

puente = iniciar_pagina("Control", "🎛️")

st.title("🎛️ Ambiente 1 · Control del operador")
st.caption("Envía órdenes al invernadero con botones, slider, texto o voz.")


def enviar(payload: dict, origen: str):
    if puente.publicar_comando(payload, origen):
        st.toast(f"Enviado: {payload}", icon="📤")
    else:
        st.toast("Sin conexión con el broker MQTT", icon="⚠️")


# ------------------------------------------------------------------ estado
@st.fragment(run_every=2)
def panel_estado():
    s = puente.snapshot()
    d = s.ultimo
    if not s.en_vivo:
        st.warning("Sin datos recientes del invernadero. Inicia la simulación en Wokwi (▶) y revisa el topic base.")
    c = st.columns(5)
    c[0].metric("Bomba de riego", "💧 ENCENDIDA" if d.get("bomba") else "⚪ apagada" if d else "—")
    c[1].metric("Lámpara", "💡 ENCENDIDA" if d.get("lampara") else "⚪ apagada" if d else "—")
    c[2].metric("Ventana", f"{d['ventana']} %" if "ventana" in d else "—")
    c[3].metric("Modo", {"auto": "🤖 automático", "manual": "🖐️ manual"}.get(d.get("modo"), "—"))
    c[4].metric("Último dato", f"hace {s.edad:.0f} s" if s.edad is not None else "—")


panel_estado()

st.divider()

# ------------------------------------------------------------------ botones y slider
st.subheader("🖐️ Control manual (botones y slider)")
st.caption("Cualquier orden manual sobre un actuador pone el sistema en modo manual.")

colb, coll, colv = st.columns(3)
with colb:
    st.markdown("**Bomba de riego**")
    b1, b2 = st.columns(2)
    if b1.button("Encender", key="bomba_on"):
        enviar({"bomba": True}, "botón")
    if b2.button("Apagar", key="bomba_off"):
        enviar({"bomba": False}, "botón")
with coll:
    st.markdown("**Lámpara de crecimiento**")
    l1, l2 = st.columns(2)
    if l1.button("Encender", key="lampara_on"):
        enviar({"lampara": True}, "botón")
    if l2.button("Apagar", key="lampara_off"):
        enviar({"lampara": False}, "botón")
with colv:
    st.markdown("**Ventana de ventilación**")
    st.slider(
        "Apertura (%)",
        0,
        100,
        0,
        5,
        key="slider_ventana",
        on_change=lambda: enviar({"ventana": int(st.session_state["slider_ventana"])}, "slider"),
    )

m1, m2, _ = st.columns([1, 1, 4])
if m1.button("🤖 Modo automático", key="modo_auto"):
    enviar({"modo": "auto"}, "botón")
if m2.button("🖐️ Modo manual", key="modo_manual"):
    enviar({"modo": "manual"}, "botón")

st.divider()


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


ctexto, cvoz = st.columns(2)

with ctexto:
    st.subheader("⌨️ Comandos de texto")
    st.caption("Ejemplos: «enciende la bomba», «abre la ventana al 50 por ciento», «apaga la luz y riega las plantas».")
    with st.form("form_texto", clear_on_submit=True):
        texto = st.text_input("Escribe una orden", placeholder="enciende la lámpara")
        if st.form_submit_button("Enviar"):
            if texto.strip():
                st.session_state["fb_texto"] = procesar_orden(texto, "texto")
    mostrar_feedback("fb_texto")

with cvoz:
    st.subheader("🎤 Comandos de voz")
    st.caption("Presiona el micrófono, di la orden en español y detén la grabación.")
    audio = st.audio_input("Graba tu orden", key="audio_orden")
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

st.divider()


# ------------------------------------------------------------------ bitácora
@st.fragment(run_every=3)
def bitacora():
    with st.expander("📜 Bitácora de comandos enviados", expanded=False):
        filas = puente.snapshot().bitacora
        if filas:
            st.dataframe(pd.DataFrame(filas), hide_index=True)
        else:
            st.caption("Aún no has enviado comandos.")


bitacora()
