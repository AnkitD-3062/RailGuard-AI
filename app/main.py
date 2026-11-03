from __future__ import annotations

import logging
from pathlib import Path
import time
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.services.analyzer import analyse_video

BASE_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = BASE_DIR / "app" / "static"
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
logger = logging.getLogger(__name__)

app = FastAPI(title="RailGuard AI", version="0.1.0")
# Allow the dashboard to call the local API when index.html is opened directly
# from VS Code or the file system. Normal dashboard use remains same-origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["null"],
    allow_methods=["POST"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _remove_upload(path: Path) -> None:
    """Delete after OpenCV has released Windows' transient video-file lock."""
    time.sleep(2)
    for attempt in range(20):
        try:
            path.unlink(missing_ok=True)
            return
        except OSError as error:
            if attempt == 19:
                logger.warning("Could not remove temporary upload %s: %s", path, error)
                return
            time.sleep(0.5)


@app.exception_handler(Exception)
async def unexpected_error_handler(_, error: Exception) -> JSONResponse:
    """Return JSON for every unexpected failure so the browser never parses HTML as JSON."""
    return JSONResponse(status_code=500, content={"detail": f"Server error: {error}"})


@app.get("/")
def dashboard() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html", headers={"Cache-Control": "no-store"})


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/analyse")
async def analyse(
    background_tasks: BackgroundTasks, file: UploadFile = File(...)
) -> dict[str, object]:
    suffix = Path(file.filename or "video.mp4").suffix.lower() or ".mp4"
    # Windows browsers frequently label a valid local video as
    # application/octet-stream. Accept known video extensions instead of
    # rejecting a user-selected file solely because of that generic MIME type.
    allowed_suffixes = {".mp4", ".avi", ".mov", ".webm", ".mkv", ".m4v", ".mpeg", ".mpg"}
    if suffix not in allowed_suffixes:
        raise HTTPException(
            status_code=415,
            detail="Upload an MP4, AVI, MOV, WebM, MKV, MPEG, or MPG video.",
        )

    destination = UPLOAD_DIR / f"{uuid4()}{suffix}"
    content = await file.read()
    if len(content) > 200 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Please use a video smaller than 200 MB.")
    destination.write_bytes(content)
    # Do not delete in this request: Windows can retain a codec handle briefly.
    background_tasks.add_task(_remove_upload, destination)

    try:
        return analyse_video(destination).as_dict()
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        # Keep API responses in JSON even when a video codec or ML dependency
        # fails, so the dashboard can show a useful message instead of a JSON
        # parsing error.
        raise HTTPException(status_code=500, detail=f"Analysis failed: {error}") from error
