"""Genera examples/plantilla.png: tarjeta de acceso neutra (formato ID-1) para la demo."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONT = ROOT / "assets" / "fonts" / "DejaVuSans-Bold.ttf"
OUT_DIR = ROOT / "examples"

# ID-1 (85,6 × 54 mm) a ~300 ppp
W, H = 1012, 638
RADIUS = 40
BAND = (31, 78, 140)
ACCENT = (242, 169, 0)
TEXT_LIGHT = (255, 255, 255)
TEXT_DARK = (40, 44, 52)
GREY = (205, 210, 218)


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT), size)


def main() -> None:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((0, 0, W - 1, H - 1), RADIUS, fill=(250, 251, 253))

    # Banda superior con el nombre ficticio
    band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(band).rounded_rectangle((0, 0, W - 1, 200), RADIUS, fill=BAND)
    ImageDraw.Draw(band).rectangle((0, 160, W - 1, 200), fill=BAND)
    img.alpha_composite(band)
    draw.rectangle((0, 200, W - 1, 214), fill=ACCENT)
    draw.text((48, 52), "EMPRESA DEMO", font=font(54), fill=TEXT_LIGHT)
    draw.text((50, 122), "CONTROL DE ACCESO", font=font(30), fill=(200, 215, 235))

    # Hueco para la foto
    draw.rounded_rectangle((48, 262, 288, 562), 16, fill=GREY)
    draw.ellipse((118, 300, 218, 400), fill=(170, 177, 189))
    draw.pieslice((88, 410, 248, 570), 180, 360, fill=(170, 177, 189))

    # Zona del código (el editor lo dibuja a partir de text_x/text_y)
    draw.text((340, 270), "Nº DE TARJETA", font=font(28), fill=(110, 118, 130))
    draw.line((340, 470, W - 60, 470), fill=GREY, width=3)
    draw.text((340, 495), "Válida en todas las sedes", font=font(26), fill=TEXT_DARK)
    draw.text((340, 535), "Uso personal e intransferible", font=font(22), fill=(110, 118, 130))

    OUT_DIR.mkdir(exist_ok=True)
    img.save(OUT_DIR / "plantilla.png")
    meta = {
        "fondo": "plantilla.png",
        "width": W,
        "height": H,
        "text_x": 336,
        "text_y": 382,
        "font_size": 120,
        "fill": list(TEXT_DARK),
        "prefijo": "A-",
        "digitos": 4,
    }
    (OUT_DIR / "tarjeta_meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"OK: {OUT_DIR / 'plantilla.png'}")


if __name__ == "__main__":
    main()
