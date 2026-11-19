from PIL import Image

from core import diagnostico, vision


def test_semaforo_ok():
    d = {"temp": 24, "hum": 60, "suelo": 55, "luz": 70}
    a = diagnostico.evaluar(d)
    assert diagnostico.nivel_global(a) == diagnostico.OK


def test_semaforo_suelo_seco_es_critico():
    a = diagnostico.evaluar({"temp": 24, "hum": 60, "suelo": 10, "luz": 70}, {"suelo": 35})
    assert diagnostico.nivel_global(a) == diagnostico.CRITICO


def test_semaforo_temperatura_alta_es_atencion():
    a = diagnostico.evaluar({"temp": 33, "hum": 60, "suelo": 60, "luz": 70}, {"temp": 28})
    assert diagnostico.nivel_global(a) == diagnostico.ATENCION


def test_sin_datos():
    assert diagnostico.nivel_global(diagnostico.evaluar({})) == diagnostico.ATENCION


def test_imagen_verde_es_sana():
    r = vision.indice_salud(Image.new("RGB", (64, 64), (40, 160, 40)))
    assert r["salud"] > 0.9


def test_imagen_amarilla_es_estres():
    r = vision.indice_salud(Image.new("RGB", (64, 64), (210, 190, 30)))
    assert r["salud"] is not None and r["salud"] < 0.2 and r["amarillo"] > 0.8


def test_imagen_gris_sin_vegetacion():
    assert vision.indice_salud(Image.new("RGB", (64, 64), (128, 128, 128)))["salud"] is None


def test_recomendacion_riego_si_estres_y_suelo_seco():
    assert vision.recomendar(0.3, 20, 35)["regar"] is True


def test_recomendacion_no_riega_si_suelo_humedo():
    assert vision.recomendar(0.3, 80, 35)["regar"] is False


def test_recomendacion_planta_sana():
    assert vision.recomendar(0.9, 20, 35)["regar"] is False
