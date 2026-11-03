"""Convert CrowdHuman ODGT annotations into a one-class YOLO detection dataset.

CrowdHuman has separate full-body, visible-region and head annotations. This
converter intentionally uses vbox (visible body) so training rewards the model
for recognising a person even when another passenger hides part of their body.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import cv2


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, required=True, help="Unzipped CrowdHuman folder")
    parser.add_argument("--train-annotations", type=Path, required=True)
    parser.add_argument("--val-annotations", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("datasets/railcrowd"))
    return parser.parse_args()


def index_images(raw_dir: Path) -> dict[str, Path]:
    images: dict[str, Path] = {}
    for extension in ("*.jpg", "*.jpeg", "*.png"):
        for image in raw_dir.rglob(extension):
            images[image.stem] = image
    return images


def yolo_line(box: list[float], image_width: int, image_height: int) -> str | None:
    x, y, width, height = box
    if width <= 1 or height <= 1:
        return None
    x_center = (x + width / 2) / image_width
    y_center = (y + height / 2) / image_height
    return f"0 {x_center:.6f} {y_center:.6f} {width / image_width:.6f} {height / image_height:.6f}"


def convert_split(annotation_path: Path, split: str, image_index: dict[str, Path], output_dir: Path) -> int:
    image_destination = output_dir / "images" / split
    label_destination = output_dir / "labels" / split
    image_destination.mkdir(parents=True, exist_ok=True)
    label_destination.mkdir(parents=True, exist_ok=True)
    converted = 0

    for raw_record in annotation_path.read_text(encoding="utf-8").splitlines():
        record = json.loads(raw_record)
        image_id = record["ID"]
        source = image_index.get(image_id)
        if source is None:
            continue
        image = cv2.imread(str(source))
        if image is None:
            continue
        height, width = image.shape[:2]
        lines: list[str] = []
        for person in record.get("gtboxes", []):
            if person.get("tag") != "person" or person.get("extra", {}).get("ignore", 0):
                continue
            line = yolo_line(person["vbox"], width, height)
            if line:
                lines.append(line)
        if not lines:
            continue
        shutil.copy2(source, image_destination / source.name)
        (label_destination / f"{source.stem}.txt").write_text("\n".join(lines), encoding="utf-8")
        converted += 1
    return converted


def main() -> None:
    args = parse_arguments()
    image_index = index_images(args.raw_dir)
    train_count = convert_split(args.train_annotations, "train", image_index, args.output_dir)
    val_count = convert_split(args.val_annotations, "val", image_index, args.output_dir)
    print(f"Converted {train_count} training and {val_count} validation images to {args.output_dir}")


if __name__ == "__main__":
    main()
