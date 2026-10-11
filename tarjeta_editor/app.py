from __future__ import annotations

import base64
import os
import sys
from pathlib import Path

from nicegui import native, ui
from PIL import Image

from .assets import assets_dir, load_meta, output_dir, resolve_fondo, save_meta, validate_meta
from .render import format_codigo, open_fondo, parse_num, preview_png_bytes, render_range, render_to_file

APP_TITLE = "Editor de tarjetas de acceso"
DEFAULT_NUM = 1


def _data_url(png: bytes) -> str:
    b64 = base64.b64encode(png).decode("ascii")
    return f"data:image/png;base64,{b64}"


def build_page() -> None:
    try:
        meta_state: dict = load_meta()
        fondo_path = resolve_fondo()
    except (FileNotFoundError, ValueError) as exc:
        ui.label(str(exc)).classes("text-red")
        return

    with Image.open(fondo_path) as fondo_img:
        fw, fh = fondo_img.size
    ejemplo = format_codigo(DEFAULT_NUM, meta_state)

    ui.label(APP_TITLE).classes("text-h5 q-mb-sm")
    # Solo el nombre de la carpeta a la vista (capturas sin rutas locales); la ruta completa en el tooltip
    ui.label(f"Plantilla: {fondo_path.name} ({fw}×{fh}) · carpeta: {assets_dir().name}").classes(
        "text-caption text-grey"
    ).tooltip(str(assets_dir()))

    with ui.row().classes("w-full q-gutter-md items-start"):
        with ui.column().classes("w-80"):
            codigo_input = ui.input("Código en vista previa", value=ejemplo).classes("w-full")

            with ui.row().classes("w-full no-wrap q-gutter-sm"):
                prefijo_input = ui.input("Prefijo", value=meta_state["prefijo"]).classes("col")
                digitos_input = ui.number(
                    "Dígitos (0 = sin ceros)", value=meta_state["digitos"], min=0, max=10, precision=0
                ).classes("col")

            ui.label("Posición X (text_x)").classes("text-caption q-mt-sm")
            slider_x = ui.slider(min=0, max=fw, value=int(meta_state["text_x"])).classes("w-full")

            ui.label("Posición Y (text_y)").classes("text-caption")
            slider_y = ui.slider(min=0, max=fh, value=int(meta_state["text_y"])).classes("w-full")

            ui.label("Tamaño de fuente").classes("text-caption")
            slider_size = ui.slider(min=24, max=320, value=int(meta_state["font_size"])).classes("w-full")

            fill = meta_state.get("fill", [15, 15, 15])
            color_picker = ui.color_input(
                "Color texto",
                value=f"#{fill[0]:02x}{fill[1]:02x}{fill[2]:02x}",
            ).classes("w-full")

            def refresh_preview() -> None:
                try:
                    num = parse_num(codigo_input.value or str(DEFAULT_NUM), meta_state["prefijo"])
                    codigo = format_codigo(num, meta_state)
                except ValueError as exc:
                    status.text = str(exc)
                    status.classes(replace="text-red text-caption")
                    return
                png = preview_png_bytes(codigo, meta_state)
                preview_image.set_source(_data_url(png))
                status.text = ""
                status.classes(replace="text-caption")

            def on_meta_change() -> None:
                meta_state["text_x"] = int(slider_x.value)
                meta_state["text_y"] = int(slider_y.value)
                meta_state["font_size"] = int(slider_size.value)
                hex_color = (color_picker.value or "#0f0f0f").lstrip("#")
                if len(hex_color) == 6:
                    meta_state["fill"] = [
                        int(hex_color[0:2], 16),
                        int(hex_color[2:4], 16),
                        int(hex_color[4:6], 16),
                    ]
                candidate = {
                    **meta_state,
                    "prefijo": (prefijo_input.value or "").strip(),
                    "digitos": int(digitos_input.value or 0),
                }
                try:
                    meta_state.update(validate_meta(candidate))
                except ValueError as exc:
                    status.text = str(exc)
                    status.classes(replace="text-red text-caption")
                    return
                refresh_preview()

            slider_x.on("update:model-value", lambda _: on_meta_change())
            slider_y.on("update:model-value", lambda _: on_meta_change())
            slider_size.on("update:model-value", lambda _: on_meta_change())
            color_picker.on("update:model-value", lambda _: on_meta_change())
            prefijo_input.on("update:model-value", lambda _: on_meta_change())
            digitos_input.on("update:model-value", lambda _: on_meta_change())
            codigo_input.on("update:model-value", lambda _: refresh_preview())

            def guardar_meta() -> None:
                save_meta(meta_state, fondo_path, (fw, fh))
                ui.notify("Configuración guardada en tarjeta_meta.json", type="positive")

            ui.button("Guardar configuración", on_click=guardar_meta).classes("w-full")

            ui.separator().classes("q-my-md")
            ui.label("Generar una").classes("text-subtitle2")

            def export_one() -> None:
                path = _export_one(meta_state, codigo_input, status)
                if path:
                    _refresh_downloads(download_list, _latest_outputs(5))

            ui.button("Exportar vista previa", on_click=export_one).classes("w-full")

            ui.separator().classes("q-my-md")
            ui.label("Generar lote").classes("text-subtitle2")
            desde_in = ui.number("Desde", value=DEFAULT_NUM, min=0, precision=0).classes("w-full")
            hasta_in = ui.number("Hasta", value=DEFAULT_NUM, min=0, precision=0).classes("w-full")

            def generar_lote() -> None:
                try:
                    d = int(desde_in.value)
                    h = int(hasta_in.value)
                    paths = render_range(d, h, meta_state)
                except (ValueError, TypeError) as exc:
                    status.text = str(exc)
                    status.classes(replace="text-red text-caption")
                    ui.notify(str(exc), type="negative")
                    return
                status.text = f"{len(paths)} archivo(s) en {output_dir()}"
                status.classes(replace="text-positive text-caption")
                ui.notify(f"Generadas {len(paths)} tarjetas", type="positive")
                _refresh_downloads(download_list, _latest_outputs(5))

            ui.button("Generar lote", on_click=generar_lote).classes("w-full")

            ui.separator().classes("q-my-md")
            ui.label(f"Salida: {output_dir().name}/").classes("text-caption").tooltip(str(output_dir()))
            download_list = ui.column().classes("w-full")
            status = ui.label("").classes("text-caption")

        with ui.column().classes("col-grow"):
            ui.label("Clic en la imagen para mover el ancla (text_x, text_y).").classes(
                "text-caption q-mb-sm"
            )
            preview_image = ui.interactive_image(_data_url(preview_png_bytes(ejemplo, meta_state)))
            preview_image.style(f"max-width: {min(fw, 960)}px; width: 100%;")

            def on_image_mouse(e) -> None:
                meta_state["text_x"] = int(round(e.image_x))
                meta_state["text_y"] = int(round(e.image_y))
                slider_x.value = meta_state["text_x"]
                slider_y.value = meta_state["text_y"]
                refresh_preview()

            preview_image.on("mousedown", on_image_mouse)

    _refresh_downloads(download_list, _latest_outputs(5))
    refresh_preview()


def run_app(*, native_window: bool | None = None) -> None:
    frozen = bool(getattr(sys, "frozen", False))
    # Ventana native (pywebview) suele fallar en PyInstaller; el .exe abre el navegador.
    if native_window is None:
        use_native = False
    else:
        use_native = native_window
    port_raw = os.environ.get("TARJETA_EDITOR_PORT", "").strip()
    if port_raw:
        port = int(port_raw)
    elif use_native:
        port = native.find_open_port()
    else:
        port = 8765
    # Solo local por defecto: la app escribe ficheros y no tiene autenticación.
    host = os.environ.get("TARJETA_EDITOR_HOST", "").strip() or "127.0.0.1"
    run_kw: dict = {
        "title": APP_TITLE,
        "reload": False,
        "host": host,
        "port": port,
        "native": use_native,
    }
    if frozen and not use_native:
        run_kw["show"] = True
    ui.run(build_page, **run_kw)


def main() -> None:
    run_app(native_window=False)


def _export_one(meta_state: dict, codigo_input, status) -> Path | None:
    try:
        num = parse_num(codigo_input.value or str(DEFAULT_NUM), meta_state["prefijo"])
        fondo = open_fondo()
        path = render_to_file(num, meta_state, fondo)
    except (ValueError, FileNotFoundError) as exc:
        status.text = str(exc)
        status.classes(replace="text-red text-caption")
        ui.notify(str(exc), type="negative")
        return None
    status.text = f"Guardado: {path.name}"
    status.classes(replace="text-positive text-caption")
    ui.notify(f"Generada {path.name}", type="positive")
    return path


def _latest_outputs(limit: int) -> list[Path]:
    out = output_dir()
    if not out.is_dir():
        return []
    files = sorted(out.glob("Tarjeta_*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[:limit]


def _refresh_downloads(container, paths: list[Path]) -> None:
    container.clear()
    with container:
        if not paths:
            ui.label("Sin archivos recientes.").classes("text-caption")
            return
        for path in paths:
            ui.link(path.name, str(path)).classes("text-caption")


if __name__ in {"__main__", "__mp_main__"}:
    main()
