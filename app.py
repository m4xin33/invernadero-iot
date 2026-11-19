import streamlit as st

from core import config
from core.ui import iniciar_pagina

puente = iniciar_pagina("Inicio", "🌱")

st.title("🌱 Invernadero inteligente multimodal")
st.write(
    "Aplicación de interfaces multimodales que se comunica en **ambos sentidos** con un "
    "invernadero simulado en **Wokwi** (ESP32) a través de **MQTT**."
)

col1, col2 = st.columns(2)
with col1:
    st.subheader("🎛️ Ambiente 1 · Control")
    st.write(
        "Para el operador del invernadero. Modalidades: **botones**, **slider**, "
        "**texto** y **voz** en español."
    )
    st.page_link("pages/1_Control.py", label="Ir a Control", icon="🎛️")
with col2:
    st.subheader("📊 Ambiente 2 · Monitoreo y diagnóstico")
    st.write(
        "Para el agrónomo. Modalidades: **gráficas en vivo**, **umbrales**, y "
        "**imagen** (cámara o foto) para diagnosticar la planta."
    )
    st.page_link("pages/2_Monitoreo_y_diagnostico.py", label="Ir a Monitoreo", icon="📊")

st.divider()
st.subheader("Arquitectura")
st.graphviz_chart(
    """
    digraph G {
      rankdir=LR; node [shape=box, style="rounded,filled", fillcolor="#eef6ee", fontname="Helvetica"];
      wokwi [label="ESP32 en Wokwi\\nDHT22 · suelo · LDR\\nbomba · lámpara · servo"];
      broker [label="Broker MQTT\\n(HiveMQ público)", fillcolor="#fff4d6"];
      app [label="App Streamlit\\nControl · Monitoreo"];
      wokwi -> broker [label=" /sensores"];
      broker -> app;
      app -> broker [label=" /comandos"];
      broker -> wokwi;
    }
    """
)

with st.expander("¿Cómo probar el sistema?", expanded=False):
    st.markdown(
        f"""
1. Abre el proyecto en Wokwi (`wokwi/diagram.json`, `wokwi/sketch.ino`, `wokwi/libraries.txt`).
2. Cambia `TOPIC_BASE` en el sketch por tu identificador y pon **el mismo** en la barra lateral.
3. Pulsa ▶ en Wokwi y espera a ver `MQTT ... OK` en el monitor serie.
4. La barra lateral debe mostrar el invernadero en 🟢. Mueve el potenciómetro (suelo) o el LDR (luz) y observa los cambios.

**Topic actual:** `{config.base_topic()}`
"""
    )
