from __future__ import annotations

import re
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .assets import DEFAULT_META, embedded_font_path, load_meta, output_dir, resolve_fondo

MAX_BATCH = 10_000


def format_codigo(num: int, meta: dict) -> str:
    """Código impreso en la tarjeta: prefijo + número con relleno de ceros opcional."""
    if num < 0:
        raise ValueError("El número de tarjeta no puede ser negativo")
    return f"{meta.get('prefijo', '')}{num:0{int(meta.get('digitos', 0))}d}"


def parse_num(value: str, prefix: str = "") -> int:
    """Extrae el número de «193», «0193» o, con prefijo, «A193» (sin distinguir mayúsculas)."""
    text = str(value).strip()
    if prefix and text.upper().startswith(prefix.upper()):
        text = text[len(prefix) :]
    if not re.fullmatch(r"\d+", text):
        raise ValueError(f"Número de tarjeta no válido: {value}")
    return int(text)


def open_fondo(path: Path | None = None) -> Image.Image:
    """Abre la plantilla en RGB; la transparencia (esquinas redondeadas) queda en blanco."""
    with Image.open(path or resolve_fondo()) as img:
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            rgba = img.convert("RGBA")
            flat = Image.new("RGB", rgba.size, (255, 255, 255))
            flat.paste(rgba, mask=rgba.getchannel("A"))
            return flat
        return img.convert("RGB")


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path(r"C:\Windows\Fonts\ariblk.ttf"),
        Path(r"C:\Windows\Fonts\arialbd.ttf"),
        Path(r"C:\Windows\Fonts\arial.ttf"),
        embedded_font_path(),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def draw_codigo(
    img: Image.Image,
    codigo: str,
    meta: dict,
) -> Image.Image:
    out = img.copy()
    draw = ImageDraw.Draw(out)
    font = load_font(int(meta["font_size"]))
    x = float(meta["text_x"])
    y = float(meta["text_y"])
    fill = tuple(meta.get("fill", DEFAULT_META["fill"]))
    bbox = draw.textbbox((0, 0), codigo, font=font)
    th = bbox[3] - bbox[1]
    draw.text(
        (x - bbox[0], y - th / 2 - bbox[1]),
        codigo,
        font=font,
        fill=fill,
    )
    return out


def render_preview(codigo: str, meta: dict | None = None) -> Image.Image:
    meta = dict(load_meta() if meta is None else meta)
    fondo = open_fondo()
    return draw_codigo(fondo, codigo, meta)


def preview_png_bytes(codigo: str, meta: dict) -> bytes:
    img = render_preview(codigo, meta)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def render_to_file(
    num: int,
    meta: dict,
    fondo: Image.Image,
    out_dir: Path | None = None,
) -> Path:
    codigo = format_codigo(num, meta)
    img = draw_codigo(fondo, codigo, meta)
    dest = out_dir or output_dir()
    dest.mkdir(parents=True, exist_ok=True)
    out = dest / f"Tarjeta_{codigo}.png"
    img.convert("RGB").save(out)
    return out


def render_range(
    desde: int,
    hasta: int,
    meta: dict | None = None,
    out_dir: Path | None = None,
) -> list[Path]:
    if hasta < desde:
        raise ValueError("El número final debe ser >= inicial")
    if hasta - desde + 1 > MAX_BATCH:
        raise ValueError(f"Como máximo {MAX_BATCH} tarjetas por lote")
    meta = dict(load_meta() if meta is None else meta)
    fondo = open_fondo()
    paths: list[Path] = []
    for n in range(desde, hasta + 1):
        paths.append(render_to_file(n, meta, fondo, out_dir))
    return paths
