# RailGuard AI

RailGuard AI is a college-project prototype that analyses recorded station video for two warning signals:

- pedestrian crowd density; and
- movement within a configurable track-exclusion band at the bottom of the video.

It uses OpenCV's bundled HOG pedestrian detector, so it can run without downloading a large AI model. This is useful for a quick demo, but it is not sufficiently accurate or safety-certified for real railway operation.

## Run locally

Use Python 3.10 or later from this folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open `http://127.0.0.1:8000` and upload a short station/platform video.

After the first setup, the shortest way to launch it is:

```powershell
.\start.ps1
```

## Use in VS Code

1. In VS Code, select **File > Open Folder**.
2. Open this `RailGuard-AI` folder.
3. Open the integrated terminal and complete the one-time setup above.
4. Select **Terminal > Run Task > Run RailGuard AI**. The dashboard opens at `http://127.0.0.1:8000`.

## Important prototype limits

The lowermost 18% of every uploaded frame is treated as the track area. This is a visual demo assumption, not actual track recognition. Before any production setting, use authorized cameras, define camera-specific safe zones, validate performance across lighting/crowd conditions, protect video data, and retain trained human control over every safety decision.
