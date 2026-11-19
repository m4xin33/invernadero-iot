"""Prueba de humo: cada página se ejecuta sin excepciones (sin broker real)."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

RAIZ = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize(
    "ruta", ["app.py", "pages/1_Control.py", "pages/2_Monitoreo_y_diagnostico.py"]
)
def test_pagina_sin_excepciones(ruta):
    at = AppTest.from_file(str(RAIZ / ruta), default_timeout=20).run()
    assert not at.exception, [e.value for e in at.exception]
