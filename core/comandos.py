"""Intérprete de comandos en español (texto o voz transcrita).

Convierte frases como "enciende la bomba y abre la ventana al 50 por ciento"
en el JSON que entiende el firmware: ``{"bomba": True, "ventana": 50}``.
Es una función pura (sin Streamlit ni MQTT), por lo que es fácil de probar.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

ENCENDER = {
    "enciende", "encender", "encienda", "prende", "prender", "activa", "activar",
    "inicia", "iniciar", "pon", "poner", "abre", "abrir", "abra", "ventila", "ventilar",
}
APAGAR = {
    "apaga", "apagar", "apague", "desactiva", "desactivar", "deten", "detener",
    "detiene", "corta", "cortar", "cierra", "cerrar", "cierre",
}
BOMBA = {"bomba", "riego", "regar", "riega", "irrigar", "irrigacion", "agua"}
LAMPARA = {"lampara", "lamparas", "luz", "luces", "foco", "iluminacion", "bombillo"}
VENTANA = {"ventana", "ventanas", "ventilacion", "ventilar", "ventila", "techo", "cortina"}
MODO_AUTO = {"automatico", "automatica", "auto", "automaticamente"}
MODO_MANUAL = {"manual"}
VERBOS_RIEGO = {"riega", "regar", "irrigar"}


@dataclass
class Resultado:
    payload: dict = field(default_factory=dict)
    entendido: list = field(default_factory=list)
    errores: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return bool(self.payload)


def normalizar(texto: str) -> str:
    """Minúsculas, sin tildes ni signos de puntuación (conserva dígitos y %)."""
    t = unicodedata.normalize("NFD", texto.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = t.replace("%", " % ")
    return re.sub(r"[^\w\s%]", " ", t).strip()


def _interpretar_clausula(raw: str) -> tuple[dict, str | None, str | None]:
    """Devuelve (payload, descripción, error) para una cláusula."""
    c = normalizar(raw)
    if not c:
        return {}, None, None
    palabras = c.split()
    ps = set(palabras)

    if ps & MODO_AUTO:
        return {"modo": "auto"}, "Modo automático", None
    if ps & MODO_MANUAL:
        return {"modo": "manual"}, "Modo manual", None

    apagar = bool(ps & APAGAR) or palabras[0] == "para"
    encender = bool(ps & ENCENDER) or bool(ps & VERBOS_RIEGO)

    if "todo" in ps and apagar:
        return (
            {"bomba": False, "lampara": False, "ventana": 0},
            "Apagar todo (bomba, lámpara y cerrar ventana)",
            None,
        )

    if ps & VENTANA:
        m = re.search(r"\b(\d{1,3})\b", c)
        if m:
            valor = max(0, min(100, int(m.group(1))))
        elif "mitad" in ps:
            valor = 50
        elif apagar:
            valor = 0
        elif encender:
            valor = 100
        else:
            return {}, None, f"No entendí qué hacer con la ventana en: «{raw.strip()}»"
        return {"ventana": valor}, f"Ventana al {valor} %", None

    if ps & BOMBA:
        if apagar:
            return {"bomba": False}, "Apagar bomba de riego", None
        if encender:
            return {"bomba": True}, "Encender bomba de riego", None
        return {}, None, f"¿Encender o apagar la bomba? («{raw.strip()}»)"

    if ps & LAMPARA:
        if apagar:
            return {"lampara": False}, "Apagar lámpara", None
        if encender:
            return {"lampara": True}, "Encender lámpara", None
        return {}, None, f"¿Encender o apagar la lámpara? («{raw.strip()}»)"

    return {}, None, f"No reconocí ningún dispositivo en: «{raw.strip()}»"


def interpretar(texto: str) -> Resultado:
    res = Resultado()
    clausulas = re.split(r"[,;.]|\by\b|\be\b|\bluego\b|\bdespues\b|\btambien\b", texto.lower())
    for cl in clausulas:
        payload, desc, error = _interpretar_clausula(cl)
        if payload:
            res.payload.update(payload)
        if desc:
            res.entendido.append(desc)
        if error:
            res.errores.append(error)
    if not res.payload and not res.errores:
        res.errores.append("No escuché ningún comando.")
    return res
