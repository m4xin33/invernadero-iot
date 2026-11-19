import pytest

from core.comandos import interpretar


@pytest.mark.parametrize(
    "texto, esperado",
    [
        ("enciende la bomba", {"bomba": True}),
        ("Apaga la bomba", {"bomba": False}),
        ("apaga la luz", {"lampara": False}),
        ("Enciende la lámpara", {"lampara": True}),
        ("abre la ventana al 50 por ciento", {"ventana": 50}),
        ("pon la ventana al 30%", {"ventana": 30}),
        ("abre la ventana", {"ventana": 100}),
        ("cierra la ventana", {"ventana": 0}),
        ("ventana a la mitad", {"ventana": 50}),
        ("modo automático", {"modo": "auto"}),
        ("pasa a modo manual", {"modo": "manual"}),
        ("riega las plantas", {"bomba": True}),
        ("para el riego", {"bomba": False}),
        ("enciende la lámpara y abre la ventana", {"lampara": True, "ventana": 100}),
        ("apaga la luz, enciende la bomba", {"lampara": False, "bomba": True}),
        ("apaga todo", {"bomba": False, "lampara": False, "ventana": 0}),
        ("ventana al 150", {"ventana": 100}),
    ],
)
def test_comandos_validos(texto, esperado):
    r = interpretar(texto)
    assert r.payload == esperado
    assert r.ok and not r.errores


@pytest.mark.parametrize("texto", ["hola mundo", "", "   ", "la bomba", "qué hora es"])
def test_comandos_invalidos(texto):
    r = interpretar(texto)
    assert not r.ok
    assert r.errores
