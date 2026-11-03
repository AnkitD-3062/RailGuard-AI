$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python 3.10 or later is required. Install Python, then run this script again."
}

if (-not (Test-Path ".venv\\Scripts\\python.exe")) {
    python -m venv .venv
}

& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
Write-Host "Setup complete. Run .\start.ps1 to launch RailGuard AI." -ForegroundColor Green
