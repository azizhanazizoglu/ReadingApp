<#
    Builds the production2 React UI, then starts the Electron app if available.
    - Path-agnostic: can be run from any directory.
    - Uses pnpm if available and pnpm-lock.yaml exists; falls back to npm.
    - If Electron is missing, runs the Vite dev server instead.
#>

$ErrorActionPreference = 'Stop'

# Resolve important paths
$root = $PSScriptRoot
if (-not $root) { $root = (Get-Location).Path }

$reactDir = Join-Path $root 'react_ui'
$reactGuiMirror = Join-Path $root 'react_gui'
$repoRoot = Split-Path $root -Parent
$electronDir = Join-Path $repoRoot 'electron_app'
$electronStarter = Join-Path $electronDir 'start_all.ps1'

if (-not (Test-Path $reactDir)) {
    throw "React GUI directory not found: $reactDir"
}

Write-Host "Building production2/react_ui..." -ForegroundColor Cyan
Push-Location $reactDir

# Select package manager
$hasPnpmLock = Test-Path (Join-Path $reactDir 'pnpm-lock.yaml')
$pnpmCmd = Get-Command pnpm -ErrorAction SilentlyContinue
$npmCmd = Get-Command npm -ErrorAction SilentlyContinue

if ($hasPnpmLock -and $pnpmCmd) {
    Write-Host "Using pnpm" -ForegroundColor DarkGray
    pnpm install --no-frozen-lockfile
    pnpm run build
} else {
    if (-not $npmCmd) { throw "npm not found. Please install Node.js (https://nodejs.org)" }
    Write-Host "Using npm" -ForegroundColor DarkGray
    npm install
    npm run build
}

Pop-Location

if (Test-Path $electronStarter) {
    # Mirror build output to production2/react_gui so Electron loads the new UI without external changes
    try {
        if (-not (Test-Path $reactGuiMirror)) { New-Item -ItemType Directory -Path $reactGuiMirror | Out-Null }
        $srcDist = Join-Path $reactDir 'dist'
        $dstDist = Join-Path $reactGuiMirror 'dist'
        if (Test-Path $dstDist) { Remove-Item -Recurse -Force $dstDist }
        Copy-Item -Recurse -Force $srcDist $dstDist
        Write-Host "Mirrored UI build to production2/react_gui/dist" -ForegroundColor DarkGray
    } catch {
        Write-Host "Warning: Could not mirror UI build to react_gui. Electron may load legacy UI." -ForegroundColor Yellow
    }
    Write-Host "Starting Electron app..." -ForegroundColor Cyan
    Push-Location $electronDir
    & $electronStarter
    Pop-Location
} else {
    Write-Host "Electron app not found. Starting Vite dev server instead..." -ForegroundColor Yellow
    Push-Location $reactDir
    if ($hasPnpmLock -and $pnpmCmd) {
        pnpm run dev
    } else {
        npm run dev
    }
    Pop-Location
}
