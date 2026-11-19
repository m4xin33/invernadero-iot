"""Reglas agronómicas simples para el semáforo del invernadero (funciones puras)."""
from __future__ import annotations

OK, ATENCION, CRITICO = "ok", "atencion", "critico"

UMBRALES_POR_DEFECTO = {"suelo": 35, "luz": 30, "temp": 28.0}


def evaluar(datos: dict, umbrales: dict | None = None) -> list[tuple[str, str]]:
    """Devuelve una lista de (nivel, mensaje) a partir de la última lectura."""
    u = {**UMBRALES_POR_DEFECTO, **(umbrales or {})}
    alertas: list[tuple[str, str]] = []
    if not datos:
        return [(ATENCION, "Sin datos del invernadero todavía.")]

    suelo, luz, temp, hum = (datos.get(k) for k in ("suelo", "luz", "temp", "hum"))

    if suelo is not None:
        if suelo < u["suelo"]:
            alertas.append((CRITICO, f"Suelo seco ({suelo} % < {u['suelo']} %): hace falta riego."))
        elif suelo > 85:
            alertas.append((ATENCION, f"Exceso de humedad en el suelo ({suelo} %): riesgo de encharcamiento."))
    if temp is not None:
        if temp < 10:
            alertas.append((CRITICO, f"Temperatura baja ({temp} °C): riesgo de helada."))
        elif temp > u["temp"]:
            alertas.append((ATENCION, f"Temperatura alta ({temp} °C > {u['temp']} °C): ventilar."))
    if luz is not None and luz < u["luz"]:
        alertas.append((ATENCION, f"Poca luz ({luz} % < {u['luz']} %): considerar lámpara de crecimiento."))
    if hum is not None and hum > 85:
        alertas.append((ATENCION, f"Humedad ambiental alta ({hum} %): riesgo de hongos."))

    return alertas or [(OK, "Condiciones óptimas en el invernadero.")]


def nivel_global(alertas: list[tuple[str, str]]) -> str:
    niveles = {n for n, _ in alertas}
    if CRITICO in niveles:
        return CRITICO
    if ATENCION in niveles:
        return ATENCION
    return OK
