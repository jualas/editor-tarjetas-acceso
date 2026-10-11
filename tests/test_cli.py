from __future__ import annotations

from tarjeta_editor.cli import main

from .conftest import write_meta


def test_genera_una(assets, tmp_path, capsys):
    out = tmp_path / "out"
    assert main(["5", "-o", str(out)]) == 0
    assert (out / "Tarjeta_5.png").is_file()
    assert "OK: 1 tarjeta(s)" in capsys.readouterr().out


def test_rango_con_prefijo(assets, tmp_path):
    write_meta(assets, prefijo="B", font_size=40)
    out = tmp_path / "out"
    assert main(["B1", "b3", "-o", str(out)]) == 0
    assert sorted(p.name for p in out.iterdir()) == ["Tarjeta_B1.png", "Tarjeta_B2.png", "Tarjeta_B3.png"]


def test_no_reescribe_la_meta(assets, tmp_path):
    write_meta(assets, prefijo="B")
    antes = (assets / "tarjeta_meta.json").read_text(encoding="utf-8")
    main(["1", "-o", str(tmp_path / "out")])
    assert (assets / "tarjeta_meta.json").read_text(encoding="utf-8") == antes


def test_numero_invalido(assets, capsys):
    assert main(["abc"]) == 1
    assert "no válido" in capsys.readouterr().err


def test_sin_plantilla(assets, capsys):
    (assets / "plantilla.png").unlink()
    assert main(["1"]) == 1
    assert "plantilla" in capsys.readouterr().err
