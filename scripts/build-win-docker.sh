#!/usr/bin/env bash
# Genera TarjetasAcceso.exe (editor de tarjetas) en Linux (Wine dentro de Docker) para copiar a Windows.
set -euo pipefail
cd "$(dirname "$0")/.."

IMAGE="${PYINSTALLER_WIN_IMAGE:-batonogov/pyinstaller-windows:latest}"

if ! command -v docker >/dev/null; then
  echo "Se necesita Docker." >&2
  exit 1
fi

echo "Imagen: $IMAGE"
echo "Montando $(pwd) en /src ..."

docker run --rm \
  -v "$(pwd):/src" \
  -w /src \
  --entrypoint /bin/bash \
  "$IMAGE" \
  -lc "
    set -e
    pip install -q -r requirements-pack.txt
    NG=\$(python -c 'import nicegui, os; print(os.path.dirname(nicegui.__file__) + \";nicegui\", end=\"\")')
    python -m PyInstaller \
      --name TarjetasAcceso \
      --onedir \
      --noconfirm \
      --clean \
      --add-data \"\$NG\" \
      --add-data \"assets/fonts/DejaVuSans-Bold.ttf;assets/fonts\" \
      --collect-submodules nicegui \
      --collect-submodules starlette \
      --collect-submodules fastapi \
      pack_entry.py
  "

if [[ -d build || -d dist ]]; then
  if command -v sudo >/dev/null && [[ "$(stat -c '%U' dist 2>/dev/null)" == root ]]; then
    sudo chown -R "$(id -u):$(id -g)" build dist TarjetasAcceso.spec 2>/dev/null || true
  fi
fi

EXE="dist/TarjetasAcceso/TarjetasAcceso.exe"
if [[ -f "$EXE" ]]; then
  echo ""
  echo "OK: $(realpath "$EXE")"
  echo "Copia la carpeta dist/TarjetasAcceso/ (o un zip) a Windows."
  echo "Pon tu plantilla (plantilla.png o la indicada en tarjeta_meta.json) junto a TarjetasAcceso.exe."
else
  echo "No se encontró $EXE — revisa la salida de PyInstaller." >&2
  exit 1
fi
