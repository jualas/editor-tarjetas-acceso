from __future__ import annotations

import pytest
from PIL import Image, ImageChops

from tarjeta_editor.assets import DEFAULT_META
from tarjeta_editor.render import (
    MAX_BATCH,
    draw_codigo,
    format_codigo,
    open_fondo,
    parse_num,
    render_range,
)


@pytest.mark.parametrize(
    ("num", "prefijo", "digitos", "esperado"),
    [(7, "", 0, "7"), (193, "B", 0, "B193"), (42, "A-", 4, "A-0042"), (12345, "A", 3, "A12345")],
)
def test_format_codigo(num, prefijo, digitos, esperado):
    assert format_codigo(num, {"prefijo": prefijo, "digitos": digitos}) == esperado


def test_format_codigo_negativo():
    with pytest.raises(ValueError):
        format_codigo(-1, DEFAULT_META)


@pytest.mark.parametrize(
    ("valor", "prefijo", "esperado"),
    [("193", "", 193), (" 0042 ", "", 42), ("B193", "B", 193), ("a-0042", "A-", 42)],
)
def test_parse_num(valor, prefijo, esperado):
    assert parse_num(valor, prefijo) == esperado


@pytest.mark.parametrize(("valor", "prefijo"), [("", ""), ("B193", ""), ("12a", ""), ("-3", ""), ("B1", "A")])
def test_parse_num_invalido(valor, prefijo):
    with pytest.raises(ValueError):
        parse_num(valor, prefijo)


def test_transparencia_queda_en_blanco(assets):
    fondo = open_fondo()
    assert fondo.mode == "RGB"
    assert fondo.getpixel((0, 0)) == (255, 255, 255)


def test_dibuja_el_codigo_en_la_posicion(assets):
    fondo = open_fondo()
    meta = {**DEFAULT_META, "text_x": 50, "text_y": 120, "font_size": 60}
    diff = ImageChops.difference(fondo, draw_codigo(fondo, "A-0042", meta)).getbbox()
    assert diff is not None
    left, top, _, bottom = diff
    assert 45 <= left <= 60 and top < 120 < bottom


def test_lote_genera_ficheros(assets, tmp_path):
    out = tmp_path / "salida"
    meta = {**DEFAULT_META, "prefijo": "A-", "digitos": 3, "font_size": 40}
    paths = render_range(8, 10, meta, out)
    assert [p.name for p in paths] == ["Tarjeta_A-008.png", "Tarjeta_A-009.png", "Tarjeta_A-010.png"]
    assert all(Image.open(p).size == (400, 250) for p in paths)


def test_lote_rango_invertido(assets):
    with pytest.raises(ValueError, match=">="):
        render_range(5, 4, DEFAULT_META)


def test_lote_demasiado_grande(assets):
    with pytest.raises(ValueError, match="máximo"):
        render_range(1, MAX_BATCH + 1, DEFAULT_META)
