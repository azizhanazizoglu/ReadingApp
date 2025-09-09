<#
	Builds production2 React UI, then installs and starts Electron.
	Falls back to legacy react_ui build if production2 is missing.
#>

$ErrorActionPreference = 'Stop'

function Build-ReactApp($dir) {
	if (-not (Test-Path $dir)) { return $false }
	Push-Location $dir
	try {
		$usePnpm = (Test-Path (Join-Path $dir 'pnpm-lock.yaml')) -and (Get-Command pnpm -ErrorAction SilentlyContinue)
		if ($usePnpm) {
			Write-Host "Using pnpm in $dir" -ForegroundColor DarkGray
			pnpm install --no-frozen-lockfile
			pnpm run build
		} else {
			Write-Host "Using npm in $dir" -ForegroundColor DarkGray
			npm install
			npm run build
		}
		return $true
	} finally {
		Pop-Location
	}
}

# Try production2 first
$prod2 = Join-Path $PSScriptRoot '../production2/react_ui'
$legacy = Join-Path $PSScriptRoot '../react_ui'

if (-not (Build-ReactApp $prod2)) {
	Write-Host "production2/react_ui not found, building legacy react_ui..." -ForegroundColor Yellow
	if (-not (Build-ReactApp $legacy)) {
		throw "No React UI found to build."
	}
}

# Install Electron deps and start
Push-Location $PSScriptRoot
try {
	Write-Host "Installing Electron dependencies..." -ForegroundColor Cyan
	npm install
	Write-Host "Starting Electron app..." -ForegroundColor Cyan
	npm start
} finally {
	Pop-Location
}
