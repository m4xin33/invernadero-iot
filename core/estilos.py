"""Identidad visual de la app: CSS, medidores circulares y piezas HTML.

Todo el HTML se genera en una sola línea (sin sangrías) porque Markdown trata
las líneas con 4 espacios como bloque de código.
"""
from __future__ import annotations

import html
import math

import streamlit as st

# Paleta: invernadero de vidrio, hojas, agua, sol y una sola alerta
NIEBLA = "#E8EEE9"
VIDRIO = "#F8FAF7"
TINTA = "#14281F"
TINTA_SUAVE = "#5B6E63"
LINEA = "#CBD7CF"
HOJA = "#2F6B4F"
AGUA = "#2B7A9B"
SOL = "#D9A21B"
LADRILLO = "#C4452F"
AIRE = "#7D8F86"

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Familjen+Grotesk:wght@500;600;700&family=Instrument+Sans:wght@400;500;600&display=swap');

:root {{
  --niebla: {NIEBLA}; --vidrio: {VIDRIO}; --tinta: {TINTA}; --suave: {TINTA_SUAVE};
  --linea: {LINEA}; --hoja: {HOJA}; --agua: {AGUA}; --sol: {SOL}; --ladrillo: {LADRILLO};
}}

.stApp {{ background: var(--niebla); color: var(--tinta); font-family: 'Instrument Sans', sans-serif; }}
.stApp, .stApp p, .stApp label, .stApp li {{ font-family: 'Instrument Sans', sans-serif; }}
h1, h2, h3, h4 {{ font-family: 'Familjen Grotesk', sans-serif !important; color: var(--tinta); letter-spacing: -0.01em; }}
h1 {{ font-weight: 700 !important; font-size: 2.6rem !important; line-height: 1.05 !important; padding-bottom: .2rem !important; }}
h2, h3 {{ font-weight: 600 !important; }}
.block-container {{ max-width: 1120px; padding-top: 2.6rem; padding-bottom: 4rem; }}

/* barra lateral */
[data-testid="stSidebar"] {{ background: #DCE6DF; border-right: 1px solid var(--linea); }}
[data-testid="stSidebar"] .inv-marca {{ font-family: 'Familjen Grotesk', sans-serif; font-weight: 700; font-size: 1.5rem; line-height: 1; margin: .2rem 0 1rem; }}
[data-testid="stSidebar"] .inv-marca span {{ display: block; font-family: 'Instrument Sans', sans-serif; font-weight: 400; font-size: .85rem; color: var(--suave); margin-top: .35rem; }}

/* textos auxiliares */
.stCaption, [data-testid="stCaptionContainer"] {{ color: var(--suave) !important; }}
.inv-lead {{ font-size: 1.15rem; line-height: 1.5; max-width: 38rem; color: var(--suave); margin: 0 0 1.8rem; }}

/* medidores */
.inv-panel {{ background: var(--vidrio); border: 1px solid var(--linea); border-radius: 18px; padding: .6rem .4rem; margin: .4rem 0 1.4rem; }}
.inv-medidores {{ display: grid; grid-template-columns: repeat(4, 1fr); }}
.inv-medidor {{ text-align: center; padding: .6rem .4rem .9rem; border-left: 1px solid var(--linea); }}
.inv-medidor:first-child {{ border-left: 0; }}
.inv-medidor svg {{ width: 100%; max-width: 190px; height: auto; }}
.inv-medidor .nombre {{ font-family: 'Familjen Grotesk', sans-serif; font-weight: 600; font-size: 1.05rem; margin-top: -.4rem; }}
.inv-medidor .nota {{ font-size: .85rem; color: var(--suave); margin-top: .15rem; min-height: 1.2em; }}
.inv-medidor .nota.alerta {{ color: var(--ladrillo); font-weight: 500; }}
@media (max-width: 760px) {{
  .inv-medidores {{ grid-template-columns: repeat(2, 1fr); }}
  .inv-medidor:nth-child(3) {{ border-left: 0; }}
  h1 {{ font-size: 2rem !important; }}
}}

/* estado de actuadores */
.inv-estado {{ display: flex; flex-wrap: wrap; gap: .5rem 2.2rem; padding: 1rem 1.3rem; background: var(--vidrio); border: 1px solid var(--linea); border-radius: 14px; margin: .4rem 0 1.2rem; }}
.inv-estado div {{ min-width: 7.5rem; }}
.inv-estado .k {{ font-size: .82rem; color: var(--suave); }}
.inv-estado .v {{ font-family: 'Familjen Grotesk', sans-serif; font-weight: 600; font-size: 1.2rem; display: flex; align-items: center; gap: .45rem; }}
.stAppDeployButton, [data-testid="stAppDeployButton"] {{ display: none; }}
.punto {{ margin: 0 .3rem 0 .25rem; width: .62rem; height: .62rem; border-radius: 50%; display: inline-block; background: var(--suave); opacity: .45; }}
.punto.on {{ background: var(--hoja); opacity: 1; box-shadow: 0 0 0 4px rgba(47,107,79,.15); }}
.punto.agua {{ background: var(--agua); opacity: 1; box-shadow: 0 0 0 4px rgba(43,122,155,.16); }}
.punto.sol {{ background: var(--sol); opacity: 1; box-shadow: 0 0 0 4px rgba(217,162,27,.2); }}
.punto.mal {{ background: var(--ladrillo); opacity: 1; box-shadow: 0 0 0 4px rgba(196,69,47,.15); }}
.punto.espera {{ background: var(--sol); opacity: 1; }}

/* alertas */
.inv-alerta {{ border-left: 4px solid var(--hoja); background: var(--vidrio); padding: .7rem 1rem; margin: .35rem 0; border-radius: 0 10px 10px 0; line-height: 1.4; }}
.inv-alerta.atencion {{ border-left-color: var(--sol); }}
.inv-alerta.critico {{ border-left-color: var(--ladrillo); }}

/* botones */
.stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button, [data-testid="stPageLink"] a {{
  border-radius: 10px; border: 1px solid var(--tinta); background: transparent; color: var(--tinta);
  font-family: 'Instrument Sans', sans-serif; font-weight: 500; transition: background .15s, color .15s;
}}
.stButton > button:hover, .stDownloadButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover {{
  background: var(--tinta); color: var(--vidrio); border-color: var(--tinta);
}}
.stButton > button:focus-visible, input:focus-visible {{ outline: 3px solid var(--agua) !important; outline-offset: 2px; }}

/* campos */
.stTextInput input, [data-baseweb="input"] {{ background: var(--vidrio) !important; border-radius: 10px !important; }}
[data-testid="stExpander"] {{ background: var(--vidrio); border: 1px solid var(--linea); border-radius: 12px; }}
[data-testid="stTabs"] button[aria-selected="true"] {{ color: var(--hoja); }}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {{ background-color: var(--hoja); }}
hr {{ border-color: var(--linea) !important; }}

.inv-seccion {{ font-family: 'Familjen Grotesk', sans-serif; font-weight: 600; font-size: 1.45rem; margin: 2.2rem 0 .2rem; }}
.inv-ayuda {{ color: var(--suave); margin: 0 0 .9rem; max-width: 42rem; }}
.inv-sub {{ font-family: 'Familjen Grotesk', sans-serif; font-weight: 600; font-size: 1.05rem; margin-bottom: .35rem; }}
@media (prefers-reduced-motion: reduce) {{ * {{ transition: none !important; }} }}
</style>
"""


def aplicar() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


# ------------------------------------------------------------------ medidor
def _punto(cx: float, cy: float, r: float, grados: float) -> tuple[float, float]:
    a = math.radians(grados)
    return cx + r * math.cos(a), cy + r * math.sin(a)


def _arco(cx: float, cy: float, r: float, a0: float, a1: float) -> str:
    x0, y0 = _punto(cx, cy, r, a0)
    x1, y1 = _punto(cx, cy, r, a1)
    grande = 1 if (a1 - a0) > 180 else 0
    return f"M{x0:.2f} {y0:.2f}A{r} {r} 0 {grande} 1 {x1:.2f} {y1:.2f}"


def medidor(
    nombre: str,
    valor: float | None,
    unidad: str,
    minimo: float,
    maximo: float,
    color: str,
    umbral: float | None = None,
    nota: str = "",
    alerta: bool = False,
    decimales: int = 0,
) -> str:
    """Medidor circular de 270° con una marca en el umbral (HTML de una línea)."""
    cx, cy, r, inicio, barrido = 80, 78, 58, 135, 270
    fondo = _arco(cx, cy, r, inicio, inicio + barrido)
    partes = [
        '<svg viewBox="0 0 160 132" role="img" aria-label="%s">' % html.escape(nombre),
        f'<path d="{fondo}" fill="none" stroke="{LINEA}" stroke-width="11" stroke-linecap="round"/>',
    ]
    if valor is not None:
        f = max(0.0, min(1.0, (valor - minimo) / (maximo - minimo)))
        if f > 0.005:
            col = LADRILLO if alerta else color
            partes.append(
                f'<path d="{_arco(cx, cy, r, inicio, inicio + barrido * f)}" fill="none" '
                f'stroke="{col}" stroke-width="11" stroke-linecap="round"/>'
            )
    if umbral is not None:
        t = max(0.0, min(1.0, (umbral - minimo) / (maximo - minimo)))
        ang = inicio + barrido * t
        x0, y0 = _punto(cx, cy, r - 12, ang)
        x1, y1 = _punto(cx, cy, r + 12, ang)
        partes.append(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="{TINTA}" stroke-width="2.5" stroke-linecap="round"/>')
    texto = "—" if valor is None else f"{valor:.{decimales}f}"
    partes.append(
        f'<text x="{cx}" y="{cy + 8}" text-anchor="middle" font-family="Familjen Grotesk, sans-serif" '
        f'font-weight="700" font-size="32" fill="{TINTA}">{texto}</text>'
        f'<text x="{cx}" y="{cy + 27}" text-anchor="middle" font-family="Instrument Sans, sans-serif" '
        f'font-size="13" fill="{TINTA_SUAVE}">{html.escape(unidad)}</text></svg>'
    )
    clase = "nota alerta" if alerta else "nota"
    return (
        f'<div class="inv-medidor">{"".join(partes)}'
        f'<div class="nombre">{html.escape(nombre)}</div>'
        f'<div class="{clase}">{html.escape(nota)}</div></div>'
    )


def panel_medidores(d: dict, umbrales: dict | None = None) -> str:
    """Los cuatro medidores del invernadero a partir de la última lectura."""
    u = {"suelo": 35, "luz": 30, "temp": 28.0, **(umbrales or {})}
    suelo, luz, temp, hum = (d.get(k) for k in ("suelo", "luz", "temp", "hum"))
    m = [
        medidor(
            "Suelo", suelo, "% humedad", 0, 100, AGUA, u["suelo"],
            nota=("Seco, falta riego" if suelo is not None and suelo < u["suelo"] else f"Mínimo {u['suelo']} %"),
            alerta=suelo is not None and suelo < u["suelo"],
        ),
        medidor(
            "Luz", luz, "% de luz", 0, 100, SOL, u["luz"],
            nota=("Poca luz" if luz is not None and luz < u["luz"] else f"Mínimo {u['luz']} %"),
            alerta=luz is not None and luz < u["luz"],
        ),
        medidor(
            "Temperatura", temp, "°C", 0, 50, HOJA, u["temp"],
            nota=("Demasiado calor" if temp is not None and temp > u["temp"] else f"Máximo {u['temp']:g} °C"),
            alerta=temp is not None and temp > u["temp"],
            decimales=1,
        ),
        medidor(
            "Aire", hum, "% humedad", 0, 100, AIRE,
            nota=("Ambiente muy húmedo" if hum is not None and hum > 85 else "Humedad del ambiente"),
            alerta=hum is not None and hum > 85,
            decimales=0,
        ),
    ]
    return f'<div class="inv-panel"><div class="inv-medidores">{"".join(m)}</div></div>'


# ------------------------------------------------------------------ otras piezas
def alerta(nivel: str, mensaje: str) -> str:
    return f'<div class="inv-alerta {html.escape(nivel)}">{html.escape(mensaje)}</div>'


def estado_actuadores(d: dict, edad: float | None) -> str:
    def item(clave: str, valor: str, punto: str = "") -> str:
        return f'<div><div class="k">{clave}</div><div class="v"><span class="punto {punto}"></span>{valor}</div></div>'

    if not d:
        return item("Estado", "Sin datos", "espera")
    modo = {"auto": "Automático", "manual": "Manual"}.get(d.get("modo"), "—")
    ventana = d.get("ventana")
    return (
        '<div class="inv-estado">'
        + item("Bomba de riego", "Encendida" if d.get("bomba") else "Apagada", "agua" if d.get("bomba") else "")
        + item("Lámpara", "Encendida" if d.get("lampara") else "Apagada", "sol" if d.get("lampara") else "")
        + item("Ventana", "—" if ventana is None else f"Abierta {ventana} %", "on" if ventana else "")
        + item("Modo", modo, "on" if d.get("modo") == "auto" else "")
        + item("Último dato", "—" if edad is None else f"hace {edad:.0f} s")
        + "</div>"
    )


def seccion(titulo: str, ayuda: str = "") -> None:
    st.markdown(f'<div class="inv-seccion">{html.escape(titulo)}</div>', unsafe_allow_html=True)
    if ayuda:
        st.markdown(f'<div class="inv-ayuda">{html.escape(ayuda)}</div>', unsafe_allow_html=True)


def subtitulo(texto: str) -> None:
    st.markdown(f'<div class="inv-sub">{html.escape(texto)}</div>', unsafe_allow_html=True)


def lead(texto: str) -> None:
    st.markdown(f'<p class="inv-lead">{html.escape(texto)}</p>', unsafe_allow_html=True)
