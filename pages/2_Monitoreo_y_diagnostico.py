import hashlib

import pandas as pd
import streamlit as st
from PIL import Image, ImageOps

from core import config, diagnostico, vision
from core.ui import iniciar_pagina

puente = iniciar_pagina("Monitoreo", "📊")

st.title("📊 Ambiente 2 · Monitoreo y diagnóstico")
st.caption("Vista del agrónomo: sensores en vivo, umbrales del modo automático y diagnóstico por imagen.")


# ------------------------------------------------------------------ panel en vivo
@st.fragment(run_every=2)
def panel_vivo():
    s = puente.snapshot()
    d = s.ultimo
    if not s.en_vivo:
        st.info("Esperando datos del invernadero (Wokwi)…")

    alertas = diagnostico.evaluar(d, d.get("umbrales"))
    nivel = diagnostico.nivel_global(alertas)
    icono = {"ok": "🟢", "atencion": "🟡", "critico": "🔴"}[nivel]
    st.subheader(f"{icono} Estado del invernadero")
    mostrar = {"ok": st.success, "atencion": st.warning, "critico": st.error}
    for n, msg in alertas:
        mostrar[n](msg)

    c = st.columns(4)
    c[0].metric("🌡️ Temperatura", f"{d['temp']} °C" if "temp" in d else "—")
    c[1].metric("💨 Humedad aire", f"{d['hum']} %" if "hum" in d else "—")
    c[2].metric("🌱 Humedad suelo", f"{d['suelo']} %" if "suelo" in d else "—")
    c[3].metric("☀️ Luz", f"{d['luz']} %" if "luz" in d else "—")

    if s.historial:
        df = pd.DataFrame(s.historial)
        df["hora"] = pd.to_datetime(df["ts"], unit="s", utc=True).dt.tz_convert(config.ZONA_HORARIA)
        df = df.set_index("hora")
        g1, g2 = st.columns(2)
        with g1:
            st.caption("Suelo y luz (%)")
            st.line_chart(df[[c for c in ("suelo", "luz") if c in df]], height=220)
        with g2:
            st.caption("Temperatura (°C) y humedad del aire (%)")
            st.line_chart(df[[c for c in ("temp", "hum") if c in df]], height=220)
        st.download_button(
            "⬇️ Descargar historial (CSV)",
            df.reset_index().to_csv(index=False).encode("utf-8"),
            file_name="historial_invernadero.csv",
            mime="text/csv",
        )


panel_vivo()

st.divider()

# ------------------------------------------------------------------ umbrales
st.subheader("⚙️ Umbrales del modo automático")
actuales = puente.snapshot().ultimo.get("umbrales", {})
u1, u2, u3 = st.columns(3)
u_suelo = u1.slider("Humedad mínima de suelo (%)", 0, 100, int(actuales.get("suelo", 35)), key="u_suelo")
u_luz = u2.slider("Luz mínima (%)", 0, 100, int(actuales.get("luz", 30)), key="u_luz")
u_temp = u3.slider("Temperatura máxima (°C)", 15.0, 45.0, float(actuales.get("temp", 28.0)), 0.5, key="u_temp")
if st.button("📤 Enviar umbrales al invernadero"):
    ok = puente.publicar_comando(
        {"umbral_suelo": int(u_suelo), "umbral_luz": int(u_luz), "umbral_temp": float(u_temp)}, "umbrales"
    )
    st.toast("Umbrales enviados" if ok else "Sin conexión con el broker MQTT", icon="📤" if ok else "⚠️")

st.divider()

# ------------------------------------------------------------------ imagen
st.subheader("🌿 Diagnóstico de la planta por imagen")
tab_cam, tab_up = st.tabs(["📷 Cámara", "📁 Subir foto"])
with tab_cam:
    foto = st.camera_input("Toma una foto de la planta")
with tab_up:
    archivo = st.file_uploader("Sube una foto", type=["png", "jpg", "jpeg", "webp"])

fuente = foto or archivo
if fuente is None:
    st.caption("Toma o sube una foto de una hoja o planta para analizarla.")
else:
    bytes_img = fuente.getvalue()
    imagen = ImageOps.exif_transpose(Image.open(fuente))
    resultado = vision.indice_salud(imagen)
    ult = puente.snapshot().ultimo
    rec = vision.recomendar(resultado["salud"], ult.get("suelo"), u_suelo)

    cimg, cres = st.columns([1, 2])
    with cimg:
        st.image(imagen, caption="Imagen analizada")
    with cres:
        if resultado["salud"] is None:
            st.warning(rec["texto"])
        else:
            m = st.columns(3)
            m[0].metric("🟢 Verde", f"{resultado['verde']:.0%}")
            m[1].metric("🟡 Amarillo", f"{resultado['amarillo']:.0%}")
            m[2].metric("🟤 Marrón", f"{resultado['marron']:.0%}")
            st.progress(min(1.0, resultado["salud"]), text=f"Índice de salud: {resultado['salud']:.0%}")
            (st.success if not rec["regar"] and resultado["salud"] >= 0.7 else st.warning)(rec["texto"])
            if rec["regar"]:
                st.button(
                    "💧 Aplicar riego recomendado",
                    on_click=lambda: puente.publicar_comando({"bomba": True}, "diagnóstico por imagen"),
                )

        clave = config.api_key_anthropic()
        if clave:
            huella = hashlib.md5(bytes_img).hexdigest()
            if st.button("🤖 Pedir segunda opinión a Claude"):
                contexto = {k: ult.get(k) for k in ("temp", "hum", "suelo", "luz")}
                with st.spinner("Consultando a Claude…"):
                    st.session_state["ia"] = {"huella": huella, "texto": vision.analizar_con_claude(imagen, contexto, clave)}
            ia = st.session_state.get("ia")
            if ia and ia["huella"] == huella:
                st.info(ia["texto"])
        else:
            st.caption("Opcional: agrega una API key de Anthropic (barra lateral → Opciones avanzadas) para una segunda opinión con IA.")
