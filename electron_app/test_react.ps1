# Wrapper to run the root test_react.ps1 from electron_app folder
$root = Split-Path -Path $PSScriptRoot -Parent
& (Join-Path $root 'test_react.ps1')
