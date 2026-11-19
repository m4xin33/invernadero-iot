"""Punto de entrada: define el menú lateral con nombres y tildes correctos."""
import streamlit as st

st.set_page_config(page_title="Invernadero", page_icon=":material/eco:", layout="wide")

navegacion = st.navigation(
    [
        st.Page("inicio.py", title="Inicio", icon=":material/home:", default=True),
        st.Page("pages/1_Control.py", title="Control", icon=":material/tune:"),
        st.Page("pages/2_Monitoreo_y_diagnostico.py", title="Monitoreo y diagnóstico", icon=":material/monitoring:"),
    ]
)
navegacion.run()
