import streamlit as st

from core import config, estilos
from core.ui import iniciar_pagina

puente = iniciar_pagina("Inicio")

st.title("Tu invernadero, en vivo")
estilos.lead(
    "Lee los sensores de un invernadero simulado en Wokwi y dale órdenes "
    "con botones, texto, voz o una foto de la planta."
)


@st.fragment(run_every=2)
def medidores():
    s = puente.snapshot()
    st.markdown(estilos.panel_medidores(s.ultimo, s.ultimo.get("umbrales")), unsafe_allow_html=True)
    if not s.en_vivo:
        st.caption("Aún no llegan datos. Inicia la simulación en Wokwi y revisa que el topic base sea el mismo.")


medidores()

c1, c2 = st.columns(2, gap="large")
with c1:
    estilos.subtitulo("Control")
    st.write("Enciende la bomba y la lámpara, abre la ventana o cambia de modo. Funciona con botones, texto escrito o tu voz.")
    st.page_link("pages/1_Control.py", label="Abrir control", icon=":material/tune:")
with c2:
    estilos.subtitulo("Monitoreo y diagnóstico")
    st.write("Revisa las gráficas, ajusta los umbrales del modo automático y analiza una foto de la planta.")
    st.page_link("pages/2_Monitoreo_y_diagnostico.py", label="Abrir monitoreo", icon=":material/monitoring:")

estilos.seccion("Cómo se conecta")
with st.expander("Ver el recorrido de los datos"):
    st.graphviz_chart(
        f"""
        digraph G {{
          rankdir=LR; bgcolor="transparent";
          node [shape=box, style="rounded,filled", fillcolor="{estilos.VIDRIO}", color="{estilos.LINEA}",
                fontname="Helvetica", fontcolor="{estilos.TINTA}"];
          edge [color="{estilos.HOJA}", fontname="Helvetica", fontcolor="{estilos.TINTA_SUAVE}"];
          wokwi [label="ESP32 en Wokwi\\nDHT22, suelo, luz\\nbomba, lámpara, servo"];
          broker [label="Broker MQTT\\n(HiveMQ público)", fillcolor="#F3E6BD"];
          app [label="Esta app\\nControl y monitoreo"];
          wokwi -> broker [label="  sensores"];
          broker -> app;
          app -> broker [label="  comandos"];
          broker -> wokwi;
        }}
        """
    )
    st.markdown(
        f"""
1. Wokwi publica las lecturas cada 2 segundos en `{config.base_topic()}/sensores`.
2. Esta app las recibe y las muestra en los medidores.
3. Cuando das una orden, la app la publica en `{config.base_topic()}/comandos` y Wokwi la ejecuta.
"""
    )
