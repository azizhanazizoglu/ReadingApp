<#
	Builds the React UI, then starts the Electron app.
	- Path-agnostic: can be run from any directory.
	- Uses pnpm if available and pnpm-lock.yaml exists; falls back to npm.
#>

$ErrorActionPreference = 'Stop'

$root = $PSScriptRoot
if (-not $root) { $root = (Get-Location).Path }

$reactDir = Join-Path $root 'react_ui'
$electronDir = Join-Path $root 'electron_app'

Write-Host "Building React UI..." -ForegroundColor Cyan
Push-Location $reactDir

$hasPnpmLock = Test-Path (Join-Path $reactDir 'pnpm-lock.yaml')
$pnpmCmd = Get-Command pnpm -ErrorAction SilentlyContinue
if ($hasPnpmLock -and $pnpmCmd) {
	pnpm install --no-frozen-lockfile
	pnpm run build
} else {
	npm install
	npm run build
}

Pop-Location

Write-Host "Starting Electron app..." -ForegroundColor Cyan
Push-Location $electronDir

& (Join-Path $electronDir 'start_all.ps1')

Pop-Location
