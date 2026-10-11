from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image


@pytest.fixture
def assets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Carpeta de assets aislada con una plantilla RGBA de esquina transparente."""
    img = Image.new("RGBA", (400, 250), (200, 220, 240, 255))
    img.putpixel((0, 0), (0, 0, 0, 0))
    img.save(tmp_path / "plantilla.png")
    for var in ("TARJETA_PLANTILLA", "TARJETA_OUTPUT_DIR"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("TARJETA_ASSETS_DIR", str(tmp_path))
    return tmp_path


def write_meta(assets: Path, **values) -> None:
    (assets / "tarjeta_meta.json").write_text(json.dumps(values), encoding="utf-8")
