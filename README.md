# RailGuard AI

RailGuard AI is a college-project prototype that analyses recorded station video for two warning signals:

- estimated pedestrian/head detections per sampled frame; and
- detections overlapping a bottom-of-frame exclusion band.

It supports the original OpenCV HOG pedestrian detector by default and an **optional CNN adapter** for a locally exported RPEE-Heads-based model. The CNN path is an integration interface, not a pretrained RPEE-Heads model or a claim that training has already been completed.

## Run locally (default HOG mode)

Use Python 3.10 or later:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000` and upload a short station/platform video. HOG mode does not require model weights.

## Optional RPEE-Heads CNN mode

RPEE-Heads is a dataset, not a drop-in inference model. Before CNN mode can produce results, you must obtain the dataset under its license/terms, train or adapt a head-detection CNN using its annotations, evaluate it, and export a compatible TorchScript checkpoint. No dataset images or trained checkpoint are included in this repository.

1. Install a PyTorch build suitable for your system using the [official PyTorch installation selector](https://pytorch.org/get-started/locally/).
2. Export the trained model as TorchScript to `models/rpee_heads_cnn.ts`, or set `RAILGUARD_CNN_CHECKPOINT` to another path.
3. The checkpoint must accept an RGB float tensor of shape `[1, 3, H, W]`, values in `[0, 1]`, and return a tensor of shape `[N, 6]`. Each row is `[x1, y1, x2, y2, confidence, class_id]` in input-image pixels; class ID `0` denotes a head.
4. Configure and launch:

```powershell
$env:RAILGUARD_DETECTOR = "cnn"
$env:RAILGUARD_CNN_CHECKPOINT = "models/rpee_heads_cnn.ts"
$env:RAILGUARD_CNN_CONFIDENCE = "0.35"
uvicorn app.main:app --reload
```

Set `RAILGUARD_DETECTOR=hog` (or unset it) to return to the original detector. The API response now includes a `detector` field identifying which detector was selected. The existing risk-score rules are unchanged and remain heuristic; they have not been calibrated for head-count outputs.

## Architecture and current limitations

- `app/main.py`: FastAPI upload endpoint and dashboard serving.
- `app/services/analyzer.py`: frame sampling, detector selection, counts and heuristic risk score.
- `app/services/cnn_detector.py`: optional TorchScript adapter for a trained head detector.
- `models/rpee_heads_cnn.ts`: expected checkpoint location; not committed/provided.

The current bottom-18% band is a demo assumption, **not actual railway-track recognition**. Head counts and pedestrian counts are not interchangeable: RPEE-Heads-trained detections should be described as head detections unless the model and evaluation support a different interpretation. Validate accuracy, crowded/occluded scenes, camera-specific zones, lighting, and runtime before making any claims. This prototype is not safety-certified and must not be used to make real railway safety decisions.
