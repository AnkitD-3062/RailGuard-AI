# RailGuard AI

RailGuard AI is a prototype railway-station safety dashboard that analyses recorded video to flag:

- crowd density on the platform; and
- movement inside a configurable low-track exclusion band.

The project uses a pretrained YOLO11n person detector, OpenCV frame sampling, and a small FastAPI web interface. It is an academic prototype and not a certified operational railway safety system.

## What the app does

- Uploads recorded video files in common formats such as MP4, AVI, MOV, and WebM.
- Samples frames from the uploaded video.
- Counts visible people using YOLO11n person detection.
- Evaluates a simple bottom-of-frame track-risk zone representing the lower 18% of the image.
- Produces a risk assessment of GREEN, YELLOW, or RED with a score from 0 to 100.
- Displays the result in a browser-based dashboard.

## Project layout

- `app/main.py` — FastAPI server and upload API.
- `app/services/analyzer.py` — video analysis logic and YOLO risk evaluation.
- `app/static/` — browser UI for uploading videos and displaying results.
- `training/` — dataset conversion and training scripts.
- `models/` — model weights used by the app.
- `data/uploads/` — uploaded videos are stored temporarily.
- `training_results/` — saved training experiment outputs.

## Setup

Requirements:

- Python 3.10 or newer
- Windows PowerShell is used in the included scripts

Run the project from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Start the dashboard:

```powershell
.\start.ps1
```

Then open:

```text
http://127.0.0.1:8000
```

## Quick usage

1. Open the dashboard in a browser.
2. Upload a short station or platform video.
3. Wait for the analysis to finish.
4. Review the computed risk score, peak crowd count, average crowd count, and track-zone intrusion count.

## Training and dataset notes

The repo includes a Kaggle pedestrian dataset conversion workflow and training scripts for future model improvement.

To convert the dataset to YOLO labels:

```powershell
python training\convert_kaggle_pedestrian.py --sample-every 8
```

To run a training job on a GPU-enabled environment:

```powershell
.\training\train_kaggle_pedestrian.ps1 -Epochs 10
```

The default app configuration uses pretrained YOLO11n weights. They are not bundled in this repository; Ultralytics downloads them on first launch unless you provide the model file locally:

```text
models/yolo11n.pt
```

You can optionally swap in a custom trained checkpoint at `models/railguard-crowdhuman.pt`; the app will prefer it automatically when present.

## Safety and deployment limits

This is a demo system for research and coursework, not a deployable railway safety product.

The current implementation uses a simplified track band based on the bottom 18% of every frame. This is a visual heuristic, not real track recognition. Before using it in a live environment, you would need:

- calibrated camera geometry;
- railway-specific safe-zone definitions;
- validation across lighting and crowd conditions;
- human oversight of every alert;
- appropriate privacy and data handling controls.

## Troubleshooting

If the dashboard cannot connect to the API:

```powershell
.\start.ps1
```

If the model is missing or invalid, verify that the weights exist in `models/` and that the environment is activated before running the app.

## Summary

RailGuard AI is a working prototype for early warning of crowd congestion and track-zone entry in station footage. It is designed as a practical demo and training project, with room for stronger model tuning and safer real-world deployment later.
