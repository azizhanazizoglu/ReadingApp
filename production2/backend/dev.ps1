$ErrorActionPreference = 'Stop'

Write-Host "Setting up venv..." -ForegroundColor Cyan
if (!(Test-Path .\.venv)) {
  python -m venv .venv
}
. .\.venv\Scripts\Activate.ps1

Write-Host "Upgrading pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip

Write-Host "Installing requirements..." -ForegroundColor Cyan
pip install -r requirements.txt

Write-Host "Starting backend (uvicorn)..." -ForegroundColor Cyan
$env:HOST = "127.0.0.1"
$env:PORT = "5100"
python -m uvicorn main:app --host $env:HOST --port $env:PORT --reload
