"""Transcripción de voz (español) a partir del WAV que entrega st.audio_input."""
from __future__ import annotations

import io


def transcribir(wav_bytes: bytes, idioma: str = "es-CO") -> tuple[str | None, str | None]:
    """Devuelve (texto, error). Usa el reconocedor web gratuito de SpeechRecognition."""
    try:
        import speech_recognition as sr
    except Exception as exc:
        return None, f"No está disponible SpeechRecognition: {exc}"

    reconocedor = sr.Recognizer()
    try:
        with sr.AudioFile(io.BytesIO(wav_bytes)) as fuente:
            audio = reconocedor.record(fuente)
        return reconocedor.recognize_google(audio, language=idioma), None
    except sr.UnknownValueError:
        return None, "No pude entender el audio. Habla más cerca del micrófono e intenta de nuevo."
    except sr.RequestError as exc:
        return None, f"El servicio de reconocimiento de voz no respondió: {exc}"
    except Exception as exc:
        return None, f"No se pudo procesar el audio: {exc}"
