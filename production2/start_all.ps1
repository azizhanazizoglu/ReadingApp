# Bootstrap backend venv, install deps, launch backend and UI (Electron or Vite)
$ErrorActionPreference = 'Stop'

$root = $PSScriptRoot
if (-not $root) { $root = (Get-Location).Path }
$backend = Join-Path $root 'backend'
$venv = Join-Path $root '.venv'
$py = Join-Path (Join-Path $venv 'Scripts') 'python.exe'
$repoRoot = Split-Path $root -Parent
$projReq = Join-Path $repoRoot 'requirements.txt'

Write-Host "[setup] Ensuring Python venv and deps..." -ForegroundColor Cyan
if (-not (Test-Path $venv)) {
  python -m venv $venv
}

& $py -m pip install -U pip | Out-Null
& $py -m pip install -r (Join-Path $backend 'requirements.txt')
if (Test-Path $projReq) {
  & $py -m pip install -r $projReq
}

# Start backend (uvicorn) in a new window
$backendCmd = "`"$py`" -m uvicorn main:app --host 127.0.0.1 --port 5100 --reload"
Write-Host "[backend] Starting: $backendCmd" -ForegroundColor Green
Start-Process powershell -ArgumentList @('-NoLogo','-NoExit','-Command',"cd `"$backend`"; $backendCmd")

# Build UI + start Electron or Vite
Write-Host "[ui] Building and starting UI..." -ForegroundColor Cyan
& (Join-Path $root 'build2run.ps1')

Write-Host "[done] Backend on http://127.0.0.1:5100; UI started." -ForegroundColor Cyan
