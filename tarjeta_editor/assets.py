from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

META_FILENAME = "tarjeta_meta.json"
DEFAULT_TEMPLATES = ("plantilla.png", "plantilla.jpg")

DEFAULT_META = {
    "text_x": 93,
    "text_y": 266,
    "font_size": 154,
    "fill": [15, 15, 15],
    "prefijo": "",
    "digitos": 0,
}

_PREFIX_RE = re.compile(r"[A-Za-z0-9_-]{0,10}")

PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parent


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def install_dir() -> Path:
    """Carpeta del ejecutable empaquetado o raíz del repo en desarrollo."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return REPO_ROOT


def bundled_resource_root() -> Path:
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", install_dir()))
    return REPO_ROOT


def embedded_font_path() -> Path:
    return bundled_resource_root() / "assets" / "fonts" / "DejaVuSans-Bold.ttf"


def assets_dir() -> Path:
    """Carpeta con la plantilla y tarjeta_meta.json.

    TARJETA_ASSETS_DIR > carpeta del .exe > examples/ del repo.
    """
    raw = os.environ.get("TARJETA_ASSETS_DIR", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    if is_frozen():
        return install_dir()
    return REPO_ROOT / "examples"


def output_dir() -> Path:
    raw = os.environ.get("TARJETA_OUTPUT_DIR", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return (assets_dir() / "generadas").resolve()


def meta_path() -> Path:
    return assets_dir() / META_FILENAME


def _stored_meta() -> dict:
    path = meta_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path.name} no es JSON válido: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} debe contener un objeto JSON")
    return data


def resolve_fondo() -> Path:
    """Plantilla: TARJETA_PLANTILLA > campo «fondo» de la meta > plantilla.png/.jpg."""
    base = assets_dir()
    raw = os.environ.get("TARJETA_PLANTILLA", "").strip()
    if raw:
        path = Path(raw).expanduser()
        path = path if path.is_absolute() else base / path
        if path.is_file():
            return path.resolve()
        raise FileNotFoundError(f"No se encuentra la plantilla indicada en TARJETA_PLANTILLA: {path}")

    fondo = str(_stored_meta().get("fondo", "")).strip()
    candidates = (fondo,) if fondo else DEFAULT_TEMPLATES
    for name in candidates:
        path = base / Path(name).name
        if path.is_file():
            return path
    raise FileNotFoundError(
        f"No se encuentra la plantilla ({' ni '.join(candidates)}) en {base}. "
        f"Indica el fichero con el campo «fondo» de {META_FILENAME} o con TARJETA_PLANTILLA."
    )


def validate_meta(meta: dict) -> dict:
    """Comprueba tipos y rangos; devuelve una copia normalizada o lanza ValueError."""
    out = dict(meta)
    for key in ("text_x", "text_y"):
        value = out.get(key)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
            raise ValueError(f"«{key}» debe ser un número >= 0 (recibido: {value!r})")
        out[key] = int(value)

    size = out.get("font_size")
    if not isinstance(size, (int, float)) or isinstance(size, bool) or not 8 <= size <= 1000:
        raise ValueError(f"«font_size» debe estar entre 8 y 1000 (recibido: {size!r})")
    out["font_size"] = int(size)

    fill = out.get("fill")
    if (
        not isinstance(fill, (list, tuple))
        or len(fill) != 3
        or not all(isinstance(c, int) and not isinstance(c, bool) and 0 <= c <= 255 for c in fill)
    ):
        raise ValueError(f"«fill» debe ser [R, G, B] con valores 0-255 (recibido: {fill!r})")
    out["fill"] = list(fill)

    prefix = out.get("prefijo")
    if not isinstance(prefix, str) or not _PREFIX_RE.fullmatch(prefix):
        raise ValueError(
            f"«prefijo» admite hasta 10 letras, números, guion o guion bajo (recibido: {prefix!r})"
        )

    digits = out.get("digitos")
    if not isinstance(digits, int) or isinstance(digits, bool) or not 0 <= digits <= 10:
        raise ValueError(f"«digitos» debe ser un entero entre 0 y 10 (recibido: {digits!r})")
    return out


def load_meta() -> dict:
    meta = dict(DEFAULT_META)
    meta.update(_stored_meta())
    return validate_meta(meta)


def save_meta(meta: dict, fondo: Path, size: tuple[int, int]) -> None:
    meta = validate_meta(meta)
    payload = {
        "fondo": fondo.name,
        "width": size[0],
        "height": size[1],
        "text_x": meta["text_x"],
        "text_y": meta["text_y"],
        "font_size": meta["font_size"],
        "fill": meta["fill"],
        "prefijo": meta["prefijo"],
        "digitos": meta["digitos"],
    }
    meta_path().write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
