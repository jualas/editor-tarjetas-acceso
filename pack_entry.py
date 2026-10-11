"""Punto de entrada para PyInstaller / nicegui-pack (Windows .exe)."""

from __future__ import annotations

import multiprocessing

from tarjeta_editor.app import run_app

if __name__ == "__main__":
    multiprocessing.freeze_support()
    run_app()
