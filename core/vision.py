"""Análisis de imagen de una planta, local (sin API) y opcionalmente con Claude.

El análisis local mide qué proporción de los píxeles "vegetales" (con color
saturado) son verdes frente a amarillos/marrones. Es una heurística sencilla
pensada para la demo: no reemplaza un diagnóstico agronómico.
"""
from __future__ import annotations

import base64
import io

import numpy as np
from PIL import Image


def indice_salud(imagen: Image.Image) -> dict:
    """Devuelve proporciones de verde/amarillo/marrón y un índice de salud 0-1."""
    img = imagen.convert("RGB").resize((256, 256))
    hsv = np.asarray(img.convert("HSV"), dtype=np.int32)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]  # PIL: cada canal en 0..255

    vegetal = (s > 50) & (v > 40)
    verde = vegetal & (h >= 55) & (h <= 130)
    amarillo = vegetal & (h >= 28) & (h < 55)
    marron = vegetal & (h < 28)

    total = int(vegetal.sum())
    cobertura = total / h.size
    if total < 0.02 * h.size:
        return {"salud": None, "verde": 0.0, "amarillo": 0.0, "marron": 0.0, "cobertura": cobertura}

    n_verde, n_amar, n_marr = int(verde.sum()), int(amarillo.sum()), int(marron.sum())
    return {
        "salud": n_verde / total,
        "verde": n_verde / total,
        "amarillo": n_amar / total,
        "marron": n_marr / total,
        "cobertura": cobertura,
    }


def recomendar(salud: float | None, suelo: float | None, umbral_suelo: float) -> dict:
    """Cruza la imagen con el sensor de suelo. Devuelve {"texto", "regar"}."""
    if salud is None:
        return {"texto": "No se detectó suficiente vegetación en la imagen. Acerca la cámara a la planta.", "regar": False}

    if salud >= 0.7:
        return {"texto": "La planta se ve sana. Mantén el plan de riego actual.", "regar": False}

    if suelo is not None and suelo < umbral_suelo + 10:
        return {
            "texto": "Hojas con signos de estrés y suelo seco: probable falta de agua. Se recomienda regar.",
            "regar": True,
        }
    return {
        "texto": (
            "Hojas con signos de estrés pero el suelo tiene humedad suficiente: "
            "revisa exceso de riego, nutrientes (clorosis), plagas o falta de luz."
        ),
        "regar": False,
    }


def a_png_bytes(imagen: Image.Image, lado_max: int = 1024) -> bytes:
    img = imagen.convert("RGB")
    img.thumbnail((lado_max, lado_max))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def analizar_con_claude(imagen: Image.Image, contexto: dict, api_key: str) -> str:
    """Consulta opcional a Claude (visión). Devuelve texto o un mensaje de error."""
    try:
        import anthropic

        cliente = anthropic.Anthropic(api_key=api_key)
        datos_b64 = base64.standard_b64encode(a_png_bytes(imagen)).decode()
        sensores = ", ".join(f"{k}={v}" for k, v in contexto.items() if v is not None) or "sin datos"
        respuesta = cliente.messages.create(
            model="claude-sonnet-5-5",
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {"type": "base64", "media_type": "image/png", "data": datos_b64},
                        },
                        {
                            "type": "text",
                            "text": (
                                "Eres un asistente agrónomo para un invernadero. Analiza la planta de la foto "
                                f"junto con estas lecturas de sensores: {sensores}. Responde en español, "
                                "en máximo 5 líneas: estado de la planta, posible causa de cualquier problema "
                                "y una acción concreta (regar, ventilar, dar luz o revisar plagas)."
                            ),
                        },
                    ],
                }
            ],
        )
        return "".join(b.text for b in respuesta.content if getattr(b, "type", "") == "text")
    except Exception as exc:  # red, clave inválida, límites, etc.
        return f"No se pudo consultar a Claude: {exc}"
