# RailGuard AI — Project Status

## Completed

- Built a FastAPI web dashboard for uploading and analysing recorded platform videos.
- Added person detection using the bundled pretrained YOLO11n model.
- Added person-only detection settings designed to preserve partially visible people in crowds.
- Added crowd-density risk scoring: GREEN, YELLOW, and RED.
- Added a prototype track-exclusion zone: the bottom 18% of each video frame.
- Added support for MP4, AVI, MOV, WebM, MKV, MPEG, and MPG uploads up to 200 MB.
- Improved upload error handling so the dashboard displays server problems clearly.
- Downloaded the Kaggle Pedestrian Dataset and converted it from AVI + CSV boxes to YOLO format.
- Prepared 187 labelled frames: 148 training images and 39 validation images.
- Included reproducible conversion and fine-tuning scripts.
- Completed a quick fine-tuning experiment: YOLO11n, one epoch, 320 px images, 30 training images (20% subset), evaluated on all 39 validation images.

## Current model

The application defaults to the pretrained YOLO11n person-detection model at `models/yolo11n.pt`. The model file is not included in this archive; Ultralytics downloads it on first launch unless supplied locally.

The quick fine-tuned checkpoint and its `results.csv` are in `training_results/kaggle-pedestrian-quick`. It is retained as evidence of an actual training run, but it is **not enabled in the dashboard** because one epoch was insufficient and its validation precision, recall, mAP@50, and mAP@50-95 were all 0. This is expected for such a very short run and is an honest result.

## Not completed

- A longer fine-tuning run (for example, 20–80 epochs on all 148 training frames, ideally with CUDA GPU access) is still needed before using a custom checkpoint.

## Honest college presentation statement

"RailGuard AI is a working railway crowd-safety prototype. It uses a pretrained YOLO11n person detector, analyses crowd density and a configurable track-safety zone, and includes a locally prepared Kaggle dataset with 148 training and 39 validation images. A short training experiment was completed and documented; longer GPU fine-tuning is proposed as future work."

## Run the dashboard

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
.\start.ps1
```

Open `http://127.0.0.1:8000`.

