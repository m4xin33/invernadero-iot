import hashlib

import pandas as pd
import streamlit as st
from PIL import Image, ImageOps

from core import config, diagnostico, estilos, vision
from core.ui import iniciar_pagina

puente = iniciar_pagina("Monitoreo")

st.title("Monitoreo y diagnóstico")
estilos.lead("Revisa cómo está el invernadero, ajusta los umbrales del modo automático y analiza una planta con una foto.")


# ------------------------------------------------------------------ panel en vivo
@st.fragment(run_every=2)
def panel_vivo():
    s = puente.snapshot()
    d = s.ultimo
    if not s.en_vivo:
        st.info("Esperando datos del invernadero en Wokwi…")

    st.markdown(estilos.panel_medidores(d, d.get("umbrales")), unsafe_allow_html=True)

    alertas = diagnostico.evaluar(d, d.get("umbrales"))
    st.markdown("".join(estilos.alerta(n, m) for n, m in alertas), unsafe_allow_html=True)

    if s.historial:
        df = pd.DataFrame(s.historial)
        df["hora"] = pd.to_datetime(df["ts"], unit="s", utc=True).dt.tz_convert(config.ZONA_HORARIA)
        df = df.set_index("hora")
        estilos.seccion("Historial")
        g1, g2 = st.columns(2, gap="large")
        with g1:
            st.caption("Suelo y luz (%)")
            cols = [c for c in ("suelo", "luz") if c in df]
            st.line_chart(df[cols], height=220, color=[estilos.AGUA, estilos.SOL][: len(cols)])
        with g2:
            st.caption("Temperatura (°C) y humedad del aire (%)")
            cols = [c for c in ("temp", "hum") if c in df]
            st.line_chart(df[cols], height=220, color=[estilos.HOJA, estilos.AIRE][: len(cols)])
        st.download_button(
            "Descargar historial (CSV)",
            df.reset_index().to_csv(index=False).encode("utf-8"),
            file_name="historial_invernadero.csv",
            mime="text/csv",
            icon=":material/download:",
        )


panel_vivo()

# ------------------------------------------------------------------ umbrales
estilos.seccion("Umbrales del modo automático", "El invernadero actúa solo cuando una lectura cruza estos valores. La marca negra de cada medidor los muestra.")
actuales = puente.snapshot().ultimo.get("umbrales", {})
u1, u2, u3 = st.columns(3, gap="large")
u_suelo = u1.slider("Humedad mínima de suelo (%)", 0, 100, int(actuales.get("suelo", 35)), key="u_suelo")
u_luz = u2.slider("Luz mínima (%)", 0, 100, int(actuales.get("luz", 30)), key="u_luz")
u_temp = u3.slider("Temperatura máxima (°C)", 15.0, 45.0, float(actuales.get("temp", 28.0)), 0.5, key="u_temp")
if st.button("Enviar umbrales", icon=":material/send:"):
    ok = puente.publicar_comando(
        {"umbral_suelo": int(u_suelo), "umbral_luz": int(u_luz), "umbral_temp": float(u_temp)}, "umbrales"
    )
    st.toast("Umbrales enviados" if ok else "No hay conexión con el broker MQTT", icon=":material/send:" if ok else ":material/warning:")

# ------------------------------------------------------------------ imagen
estilos.seccion("Diagnóstico de la planta por imagen", "Toma o sube una foto de una hoja. La app mide cuánto verde, amarillo y marrón tiene y lo cruza con la humedad del suelo.")
tab_cam, tab_up = st.tabs(["Cámara", "Subir foto"])
with tab_cam:
    foto = st.camera_input("Toma una foto de la planta", label_visibility="collapsed")
with tab_up:
    archivo = st.file_uploader("Sube una foto", type=["png", "jpg", "jpeg", "webp"], label_visibility="collapsed")

fuente = foto or archivo
if fuente is None:
    st.caption("Aún no hay ninguna imagen.")
else:
    bytes_img = fuente.getvalue()
    imagen = ImageOps.exif_transpose(Image.open(fuente))
    resultado = vision.indice_salud(imagen)
    ult = puente.snapshot().ultimo
    rec = vision.recomendar(resultado["salud"], ult.get("suelo"), u_suelo)

    cimg, cres = st.columns([1, 2], gap="large")
    with cimg:
        st.image(imagen, caption="Imagen analizada")
    with cres:
        if resultado["salud"] is None:
            st.warning(rec["texto"])
        else:
            m = st.columns(3)
            m[0].metric("Verde", f"{resultado['verde']:.0%}")
            m[1].metric("Amarillo", f"{resultado['amarillo']:.0%}")
            m[2].metric("Marrón", f"{resultado['marron']:.0%}")
            st.progress(min(1.0, resultado["salud"]), text=f"Índice de salud: {resultado['salud']:.0%}")
            (st.success if not rec["regar"] and resultado["salud"] >= 0.7 else st.warning)(rec["texto"])
            if rec["regar"]:
                st.button(
                    "Aplicar riego recomendado",
                    icon=":material/water_drop:",
                    on_click=lambda: puente.publicar_comando({"bomba": True}, "diagnóstico por imagen"),
                )

        clave = config.api_key_anthropic()
        if clave:
            huella = hashlib.md5(bytes_img).hexdigest()
            if st.button("Pedir segunda opinión a Claude", icon=":material/psychology:"):
                contexto = {k: ult.get(k) for k in ("temp", "hum", "suelo", "luz")}
                with st.spinner("Consultando a Claude…"):
                    st.session_state["ia"] = {"huella": huella, "texto": vision.analizar_con_claude(imagen, contexto, clave)}
            ia = st.session_state.get("ia")
            if ia and ia["huella"] == huella:
                st.info(ia["texto"])
        else:
            st.caption("Opcional: agrega una API key de Anthropic en la barra lateral (Opciones avanzadas) para una segunda opinión con IA.")
