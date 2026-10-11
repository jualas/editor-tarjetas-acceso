# Genera TarjetasAcceso.exe en Windows (ejecutar en PowerShell desde tarjeta-editor/).
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

if (-not (Test-Path .venv)) {
    python -m venv .venv
}
& .\.venv\Scripts\pip install -r requirements-pack.txt

$font = "assets\fonts\DejaVuSans-Bold.ttf"
& .\.venv\Scripts\nicegui-pack pack_entry.py `
    --name TarjetasAcceso `
    --onedir `
    --add-data "${font};assets\fonts"

Write-Host ""
Write-Host "Listo: dist\TarjetasAcceso\TarjetasAcceso.exe"
Write-Host "Copia tu plantilla (plantilla.png o la indicada en tarjeta_meta.json) junto al .exe."
