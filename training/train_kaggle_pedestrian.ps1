param(
    [int]$SampleEvery = 8,
    [int]$Epochs = 50
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

& $Python "$PSScriptRoot\convert_kaggle_pedestrian.py" --sample-every $SampleEvery
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $Python "$PSScriptRoot\train.py" --epochs $Epochs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$Best = Join-Path $ProjectRoot "runs\railguard\crowdhuman-yolo11s\weights\best.pt"
$ModelDir = Join-Path $ProjectRoot "models"
New-Item -ItemType Directory -Force -Path $ModelDir | Out-Null
Copy-Item $Best (Join-Path $ModelDir "railguard-crowdhuman.pt") -Force
Write-Host "Training complete. The dashboard will now use models\railguard-crowdhuman.pt"
