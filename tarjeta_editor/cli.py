from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

from .assets import load_meta, output_dir, resolve_fondo
from .render import parse_num, render_range


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Genera tarjetas de control de acceso numeradas sobre una plantilla"
    )
    parser.add_argument("desde", help="Número inicial, ej. 193 (admite el prefijo configurado: A193)")
    parser.add_argument(
        "hasta",
        nargs="?",
        default=None,
        help="Número final inclusive. Si se omite, genera solo uno.",
    )
    parser.add_argument(
        "-o",
        "--salida",
        type=Path,
        default=None,
        help="Carpeta de salida (por defecto: TARJETA_OUTPUT_DIR o <assets>/generadas)",
    )
    args = parser.parse_args(argv)

    try:
        meta = load_meta()
        fondo_path = resolve_fondo()
        inicio = parse_num(args.desde, meta["prefijo"])
        fin = parse_num(args.hasta, meta["prefijo"]) if args.hasta is not None else inicio
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    with Image.open(fondo_path) as img:
        size = img.size
    out = args.salida or output_dir()
    print(f"Plantilla: {fondo_path.name} ({size[0]}x{size[1]})")
    try:
        paths = render_range(inicio, fin, meta, out)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    for p in paths:
        print(p.name)
    print(f"OK: {len(paths)} tarjeta(s) en {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
