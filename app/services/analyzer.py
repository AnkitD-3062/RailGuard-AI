from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os
from pathlib import Path

import cv2

@dataclass
class AnalysisResult:
    sampled_frames: int
    peak_people: int
    average_people: float
    risk_level: str
    risk_score: int
    track_intrusion_frames: int
    message: str
    detector: str

    def as_dict(self) -> dict[str, object]:
        return {
            "sampled_frames": self.sampled_frames,
            "peak_people": self.peak_people,
            "average_people": self.average_people,
            "risk_level": self.risk_level,
            "risk_score": self.risk_score,
            "track_intrusion_frames": self.track_intrusion_frames,
            "message": self.message,
            "detector": self.detector,
        }

def _model_path() -> str:
    """Prefer the CrowdHuman-fine-tuned model, then fall back to YOLO11 weights.

    The fallback model is trained on COCO and gives a much stronger starting point
    than HOG-SVM. Place the result of training at models/railguard-crowdhuman.pt
    to make the application use the station-crowd-specific model automatically.
    """
    # Resolve from the project folder rather than the shell's current folder.
    # This lets the app work when it is launched through VS Code tasks too.
    project_root = Path(__file__).resolve().parents[2]
    requested = Path(os.getenv("RAILGUARD_MODEL", "models/railguard-crowdhuman.pt"))
    custom_model = requested if requested.is_absolute() else project_root / requested
    baseline_model = project_root / "models" / "yolo11n.pt"
    if custom_model.exists():
        return str(custom_model)
    if baseline_model.exists():
        return str(baseline_model)
    return "yolo11n.pt"

@lru_cache(maxsize=1)
def _load_detector(model_path: str) -> object:
    """Load YOLO once and reuse it for every video upload."""
    from ultralytics import YOLO

    return YOLO(model_path)

def _person_boxes(model: object, frame: object) -> list[tuple[int, int, int, int]]:
    """Run person-only YOLO inference with settings suited to dense crowds.

    A low confidence threshold preserves partially visible people. The higher NMS
    IoU threshold avoids suppressing two closely overlapping people too early.
    These settings need validation against local station footage before deployment.
    """
    results = model.predict(
        source=frame,
        classes=[0],  # COCO / CrowdHuman person class
        conf=0.18,
        iou=0.70,
        imgsz=960,
        verbose=False,
    )
    boxes = results[0].boxes.xyxy.cpu().tolist() if len(results[0].boxes) else []
    return [(int(x1), int(y1), int(x2), int(y2)) for x1, y1, x2, y2 in boxes]

def _risk(peak_people: int, average_people: float, intrusions: int) -> tuple[str, int, str]:
    """Turn observed counts into an explainable, conservative demo risk score."""
    crowd_score = min(70, peak_people * 7 + int(average_people * 3))
    intrusion_score = 30 if intrusions else 0
    score = min(100, crowd_score + intrusion_score)

    if intrusions:
        return "RED", max(score, 80), "Track-area movement detected — alert station security immediately."
    if score >= 55:
        return "RED", score, "Critical platform density. Open alternate exits and regulate entry."
    if score >= 28:
        return "YELLOW", score, "Crowd density rising. Deploy staff and monitor the bottleneck."
    return "GREEN", score, "Density is within the configured prototype threshold."

def analyse_video(video_path: Path, sample_every: int = 12, max_samples: int = 60) -> AnalysisResult:
    """Estimate people in a video and flag detections in the bottom track safety band.

    The track band is intentionally a configurable demo heuristic. A production installation
    must use calibrated camera-specific zones and a validated detection model.
    """

    capture = cv2.VideoCapture(str(video_path))
    try:
        is_open = capture.isOpened()
    except Exception:
        capture.release()
        raise
    if not is_open:
        capture.release()
        raise ValueError("The uploaded file could not be read as a video.")

    try:
        try:
            from ultralytics import YOLO
        except ImportError as error:
            raise RuntimeError(
                "YOLO is not installed. Run: pip install -r requirements.txt"
            ) from error

        detector_name = _model_path()
        detector = _load_detector(detector_name)
        frame_number = 0
        sampled_frames = 0
        people_counts: list[int] = []
        intrusion_frames = 0

        while sampled_frames < max_samples:
            ok, frame = capture.read()
            if not ok:
                break
            frame_number += 1
            if frame_number % sample_every:
                continue

            height, width = frame.shape[:2]
            if width > 960:
                scale = 640 / width
                frame = cv2.resize(frame, (960, int(height * scale)))
                height, width = frame.shape[:2]

            boxes = _person_boxes(detector, frame)
            people_counts.append(len(boxes))
            sampled_frames += 1

            # Demo convention: the lowest 18% of the image is the track exclusion zone.
            track_start = int(height * 0.82)
            if any(y2 >= track_start for _x1, _y1, _x2, y2 in boxes):
                intrusion_frames += 1

        if not sampled_frames:
            raise ValueError("No frames could be sampled from this video.")

        peak = max(people_counts)
        average = round(sum(people_counts) / sampled_frames, 1)
        risk_level, risk_score, message = _risk(peak, average, intrusion_frames)
        return AnalysisResult(
            sampled_frames=sampled_frames,
            peak_people=peak,
            average_people=average,
            risk_level=risk_level,
            risk_score=risk_score,
            track_intrusion_frames=intrusion_frames,
            message=message,
            detector=f"YOLO ({detector_name})",
        )
    finally:
        capture.release()
