"""Fine-tune YOLO on the converted CrowdHuman visible-person labels."""
from __future__ import annotations

import argparse
from pathlib import Path

from ultralytics import YOLO


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("training/data.yaml"))
    parser.add_argument("--model", default="yolo11s.pt", help="Use yolo11n.pt when GPU memory is tight")
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--imgsz", type=int, default=960)
    parser.add_argument("--device", default="0", help="GPU index, or cpu")
    parser.add_argument("--name", default="railguard-person", help="Folder name for the saved training run")
    parser.add_argument("--fraction", type=float, default=1.0, help="Fraction of training images to use (0-1)")
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()
    model = YOLO(args.model)
    model.train(
        data=str(args.data),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=-1,  # Let Ultralytics choose a safe batch size for the GPU.
        device=args.device,
        workers=4,
        patience=20,
        cos_lr=True,
        mosaic=0.7,
        mixup=0.1,
        close_mosaic=10,
        fraction=args.fraction,
        project="runs/railguard",
        name=args.name,
    )


if __name__ == "__main__":
    main()
