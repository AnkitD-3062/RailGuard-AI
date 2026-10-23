"""Optional adapter for a locally trained RPEE-Heads CNN checkpoint.

Checkpoint contract: TorchScript module accepting an RGB float tensor shaped
[1, 3, H, W] with values in [0, 1], and returning a tensor shaped [N, 6].
Each output row is [x1, y1, x2, y2, confidence, class_id] in input-image pixels.
Use class_id=0 for a detected head. This adapter does not train a model or
convert the RPEE-Heads annotations into a checkpoint.
"""
from __future__ import annotations

import os
from pathlib import Path

import cv2
import numpy as np


class CNNHeadDetector:
    def __init__(self, checkpoint: str | Path, confidence_threshold: float = 0.35):
        try:
            import torch
        except ImportError as exc:
            raise RuntimeError(
                "CNN mode requires PyTorch. Install it using the official PyTorch "
                "instructions for your operating system."
            ) from exc

        path = Path(checkpoint)
        if not path.is_file():
            raise RuntimeError(
                f"CNN checkpoint not found: {path}. Train/export a compatible "
                "RPEE-Heads model and set RAILGUARD_CNN_CHECKPOINT."
            )
        self.torch = torch
        self.model = torch.jit.load(str(path), map_location="cpu")
        self.model.eval()
        self.confidence_threshold = confidence_threshold

    def detectMultiScale(self, frame, **_kwargs):
        """Return OpenCV-like boxes and scores so the existing analyzer can consume them."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        tensor = self.torch.from_numpy(np.ascontiguousarray(rgb)).permute(2, 0, 1)
        tensor = tensor.float().div(255.0).unsqueeze(0)
        with self.torch.inference_mode():
            output = self.model(tensor)
        if isinstance(output, (tuple, list)):
            output = output[0]
        if not self.torch.is_tensor(output) or output.ndim != 2 or output.shape[1] != 6:
            raise RuntimeError(
                "CNN output must be a tensor of shape [N, 6]: "
                "[x1, y1, x2, y2, confidence, class_id]."
            )
        rows = output.detach().cpu().numpy()
        boxes, scores = [], []
        for x1, y1, x2, y2, score, class_id in rows:
            if int(class_id) != 0 or float(score) < self.confidence_threshold:
                continue
            x1, y1, x2, y2 = map(int, (x1, y1, x2, y2))
            if x2 <= x1 or y2 <= y1:
                continue
            boxes.append([x1, y1, x2 - x1, y2 - y1])
            scores.append(float(score))
        return np.asarray(boxes, dtype=np.int32).reshape(-1, 4), np.asarray(scores, dtype=np.float32)


def load_cnn_detector():
    checkpoint = os.getenv("RAILGUARD_CNN_CHECKPOINT", "models/rpee_heads_cnn.ts")
    threshold = float(os.getenv("RAILGUARD_CNN_CONFIDENCE", "0.35"))
    return CNNHeadDetector(checkpoint, threshold)
