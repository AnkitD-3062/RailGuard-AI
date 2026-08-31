$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".venv\\Scripts\\python.exe")) {
    Write-Host "The virtual environment is missing. Run the setup steps in README.md first." -ForegroundColor Yellow
    exit 1
}

Write-Host "Starting RailGuard AI at http://127.0.0.1:8000" -ForegroundColor Green
& .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
