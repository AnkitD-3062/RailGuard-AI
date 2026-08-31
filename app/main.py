from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.services.analyzer import analyse_video

BASE_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = BASE_DIR / "app" / "static"
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="RailGuard AI", version="0.1.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def dashboard() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/analyse")
async def analyse(file: UploadFile = File(...)) -> dict[str, object]:
    allowed_types = {"video/mp4", "video/x-msvideo", "video/quicktime", "video/webm"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=415, detail="Upload an MP4, AVI, MOV, or WebM video.")

    suffix = Path(file.filename or "video.mp4").suffix.lower() or ".mp4"
    destination = UPLOAD_DIR / f"{uuid4()}{suffix}"
    content = await file.read()
    if len(content) > 200 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Please use a video smaller than 200 MB.")
    destination.write_bytes(content)

    try:
        return analyse_video(destination).as_dict()
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    finally:
        destination.unlink(missing_ok=True)
