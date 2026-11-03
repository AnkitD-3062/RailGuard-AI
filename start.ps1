$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$Python = Join-Path $PSScriptRoot ".venv\\Scripts\\python.exe"
if (-not (Test-Path $Python)) {
    $WorkspacePython = Join-Path $PSScriptRoot "..\\..\\railguard\\.venv\\Scripts\\python.exe"
    if (Test-Path $WorkspacePython) {
        $Python = $WorkspacePython
    } else {
        Write-Host "Python environment not found. Run .\\setup.ps1 once, then retry." -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "Starting RailGuard AI at http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "Keep this terminal open while using the dashboard." -ForegroundColor Yellow
& $Python -u -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level info
