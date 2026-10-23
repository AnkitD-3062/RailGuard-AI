"""Detector backends for RailGuard-AI.

HOG remains the default for backwards compatibility. Set
RAILGUARD_DETECTOR=cnn and RAILGUARD_CNN_WEIGHTS to enable a compatible
Ultralytics YOLO head-detection checkpoint trained on RPEE-Heads.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import cv2
import numpy as np


class HOGDetector:
    """OpenCV's built-in pedestrian detector; does not require model weights."""

    def __init__(self) -> None:
        self.model = cv2.HOGDescriptor()
        self.model.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    def detect(self, frame: np.ndarray) -> list[tuple[int, int, int, int]]:
        boxes, _weights = self.model.detectMultiScale(
            frame, winStride=(8, 8), padding=(8, 8), scale=1.05
        )
        return [(int(x), int(y), int(w), int(h)) for x, y, w, h in boxes]


class CNNHeadDetector:
    """Ultralytics-backed CNN head detector using a compatible local checkpoint."""

    def __init__(self, weights_path: str) -> None:
        path = Path(weights_path).expanduser()
        if not path.is_file():
            raise FileNotFoundError(
                f"CNN weights not found at '{path}'. Download a compatible "
                "RPEE-Heads head-detection .pt checkpoint and set "
                "RAILGUARD_CNN_WEIGHTS to its path."
            )
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError(
                "CNN mode requires the 'ultralytics' package. Install requirements.txt."
            ) from exc
        self.model: Any = YOLO(str(path))
        self.confidence = float(os.getenv("RAILGUARD_CNN_CONFIDENCE", "0.25"))
        self.image_size = int(os.getenv("RAILGUARD_CNN_IMAGE_SIZE", "832"))

    def detect(self, frame: np.ndarray) -> list[tuple[int, int, int, int]]:
        results = self.model.predict(
            source=frame,
            conf=self.confidence,
            imgsz=self.image_size,
            verbose=False,
        )
        boxes_out: list[tuple[int, int, int, int]] = []
        if not results:
            return boxes_out
        boxes = results[0].boxes
        if boxes is None:
            return boxes_out
        for xyxy in boxes.xyxy.cpu().numpy():
            x1, y1, x2, y2 = (int(round(float(v))) for v in xyxy[:4])
            boxes_out.append((x1, y1, max(0, x2 - x1), max(0, y2 - y1)))
        return boxes_out


def build_detector() -> tuple[Any, str]:
    """Create the configured backend. Defaults to HOG unless CNN is explicitly enabled."""
    backend = os.getenv("RAILGUARD_DETECTOR", "hog").strip().lower()
    if backend == "hog":
        return HOGDetector(), "hog"
    if backend == "cnn":
        weights = os.getenv("RAILGUARD_CNN_WEIGHTS", "models/rpee_heads/best.pt")
        return CNNHeadDetector(weights), "cnn"
    raise ValueError("RAILGUARD_DETECTOR must be either 'hog' or 'cnn'.")
