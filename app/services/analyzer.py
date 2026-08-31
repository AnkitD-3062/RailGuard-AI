from __future__ import annotations

from dataclasses import dataclass
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

    def as_dict(self) -> dict[str, object]:
        return {
            "sampled_frames": self.sampled_frames,
            "peak_people": self.peak_people,
            "average_people": self.average_people,
            "risk_level": self.risk_level,
            "risk_score": self.risk_score,
            "track_intrusion_frames": self.track_intrusion_frames,
            "message": self.message,
        }


def _person_detector() -> cv2.HOGDescriptor:
    """Create OpenCV's built-in pedestrian detector (no model download required)."""
    detector = cv2.HOGDescriptor()
    detector.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    return detector


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


def analyse_video(video_path: Path, sample_every: int = 12, max_samples: int = 180) -> AnalysisResult:
    """Estimate people in a video and flag detections in the bottom track safety band.

    The track band is intentionally a configurable demo heuristic. A production installation
    must use calibrated camera-specific zones and a validated detection model.
    """
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise ValueError("The uploaded file could not be read as a video.")

    detector = _person_detector()
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
            scale = 960 / width
            frame = cv2.resize(frame, (960, int(height * scale)))
            height, width = frame.shape[:2]

        boxes, _weights = detector.detectMultiScale(
            frame, winStride=(8, 8), padding=(8, 8), scale=1.05
        )
        people_counts.append(len(boxes))
        sampled_frames += 1

        # Demo convention: the lowest 18% of the image is the track exclusion zone.
        track_start = int(height * 0.82)
        if any(y + h >= track_start for _x, y, _w, h in boxes):
            intrusion_frames += 1

    capture.release()
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
    )
