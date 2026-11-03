$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    throw "Create the project virtual environment first: python -m venv .venv"
}

& $python -m pip install -r (Join-Path $projectRoot "requirements.txt")
& (Join-Path $PSScriptRoot "download_crowdhuman.ps1")
& $python (Join-Path $PSScriptRoot "convert_crowdhuman.py") `
    --raw-dir (Join-Path $projectRoot "datasets\crowdhuman_raw") `
    --train-annotations (Join-Path $projectRoot "datasets\crowdhuman_raw\annotation_train.odgt") `
    --val-annotations (Join-Path $projectRoot "datasets\crowdhuman_raw\annotation_val.odgt")
& $python (Join-Path $PSScriptRoot "train.py") --epochs 80 --imgsz 960 --device 0

$bestModel = Join-Path $projectRoot "runs\railguard\crowdhuman-yolo11s\weights\best.pt"
$modelDirectory = Join-Path $projectRoot "models"
if (-not (Test-Path $bestModel)) {
    throw "Training finished without creating best.pt. Check the training output above."
}
New-Item -ItemType Directory -Path $modelDirectory -Force | Out-Null
Copy-Item -LiteralPath $bestModel -Destination (Join-Path $modelDirectory "railguard-crowdhuman.pt") -Force
Write-Host "Training complete. The RailGuard dashboard will now use models\railguard-crowdhuman.pt." -ForegroundColor Green
