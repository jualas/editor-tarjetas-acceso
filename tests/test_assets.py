from __future__ import annotations

import pytest
from PIL import Image

from tarjeta_editor.assets import DEFAULT_META, load_meta, resolve_fondo, save_meta, validate_meta

from .conftest import write_meta


def test_plantilla_por_defecto(assets):
    assert resolve_fondo() == assets / "plantilla.png"


def test_plantilla_desde_meta(assets):
    Image.new("RGB", (10, 10)).save(assets / "mi_diseno.png")
    write_meta(assets, fondo="mi_diseno.png")
    assert resolve_fondo().name == "mi_diseno.png"


def test_meta_no_puede_salir_de_la_carpeta(assets):
    write_meta(assets, fondo="../plantilla.png")
    # Solo se usa el nombre del fichero: busca plantilla.png dentro de assets
    assert resolve_fondo() == assets / "plantilla.png"


def test_variable_de_entorno_tiene_prioridad(assets, monkeypatch):
    Image.new("RGB", (10, 10)).save(assets / "otra.jpg")
    write_meta(assets, fondo="plantilla.png")
    monkeypatch.setenv("TARJETA_PLANTILLA", "otra.jpg")
    assert resolve_fondo().name == "otra.jpg"


def test_sin_plantilla_da_error_claro(assets):
    (assets / "plantilla.png").unlink()
    with pytest.raises(FileNotFoundError, match="TARJETA_PLANTILLA"):
        resolve_fondo()


def test_meta_por_defecto(assets):
    assert load_meta() == DEFAULT_META


def test_guardar_y_cargar(assets):
    meta = {**DEFAULT_META, "text_x": 10, "prefijo": "B", "digitos": 3}
    save_meta(meta, assets / "plantilla.png", (400, 250))
    loaded = load_meta()
    assert (loaded["text_x"], loaded["prefijo"], loaded["digitos"]) == (10, "B", 3)


def test_json_invalido(assets):
    (assets / "tarjeta_meta.json").write_text("{roto", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON"):
        load_meta()


@pytest.mark.parametrize(
    "cambio",
    [
        {"text_x": -1},
        {"text_y": "10"},
        {"font_size": 2},
        {"font_size": True},
        {"fill": [0, 0]},
        {"fill": [0, 0, 300]},
        {"prefijo": "con espacio"},
        {"prefijo": "<script>"},
        {"prefijo": "X" * 11},
        {"digitos": 11},
        {"digitos": 2.5},
    ],
)
def test_validacion_rechaza(cambio):
    with pytest.raises(ValueError):
        validate_meta({**DEFAULT_META, **cambio})
