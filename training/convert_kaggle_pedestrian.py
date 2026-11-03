"""Convert Kaggle's `smeschke/pedestrian-dataset` into a compact YOLO dataset.

Place the downloaded Kaggle ZIP (or its extracted contents) in
`datasets/kaggle_pedestrian_raw`, then run this script from the project root.
The source videos and their CSV bounding boxes stay untouched; output is written
to `datasets/railcrowd` for the existing training command.
"""

from __future__ import annotations

import argparse
import csv
import random
import shutil
import zipfile
from collections import defaultdict
from pathlib import Path

import cv2


PROJECT = Path(__file__).resolve().parents[1]
RAW = PROJECT / "datasets" / "kaggle_pedestrian_raw"
OUT = PROJECT / "datasets" / "railcrowd"
IMAGE_EXTENSIONS = {".avi", ".mp4", ".mov", ".mkv"}


def value(row: dict[str, str], *names: str) -> float:
    lower = {key.lower().strip(): item for key, item in row.items()}
    for name in names:
        item = lower.get(name.lower())
        if item not in (None, ""):
            return float(item)
    raise KeyError(f"Missing one of {names}; CSV columns are {list(row)}")


def frame_value(row: dict[str, str]) -> int:
    return int(value(row, "frame", "frame_number", "frameid", "frame_id", "frame no", "framenumber"))


def box(row: dict[str, str]) -> tuple[float, float, float, float]:
    """Read either left/top/width/height or xmin/ymin/xmax/ymax CSV annotations."""
    x1 = value(row, "xmin", "x_min", "left", "bbox_left", "x")
    y1 = value(row, "ymin", "y_min", "top", "bbox_top", "y")
    try:
        x2 = value(row, "xmax", "x_max", "right", "bbox_right")
        y2 = value(row, "ymax", "y_max", "bottom", "bbox_bottom")
        return x1, y1, x2 - x1, y2 - y1
    except KeyError:
        return x1, y1, value(row, "width", "w", "bbox_width"), value(row, "height", "h", "bbox_height")


def extract_zip_files() -> None:
    for archive in RAW.glob("*.zip"):
        destination = RAW / archive.stem
        if not destination.exists():
            print(f"Extracting {archive.name}")
            with zipfile.ZipFile(archive) as handle:
                handle.extractall(destination)


def find_matching_csv(video: Path) -> Path:
    candidates = list(video.parent.glob(f"{video.stem}.csv")) + list(RAW.rglob(f"{video.stem}.csv"))
    if not candidates:
        raise FileNotFoundError(f"No CSV labels found for {video.name}")
    return candidates[0]


def read_annotations(csv_path: Path) -> dict[int, list[tuple[float, float, float, float]]]:
    annotations: dict[int, list[tuple[float, float, float, float]]] = defaultdict(list)
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        for row_number, row in enumerate(csv.DictReader(handle)):
            try:
                # The Kaggle pedestrian set has one CSV row per video frame and
                # uses only x,y,w,h. Other compatible exports include frame IDs.
                try:
                    frame_id = frame_value(row)
                except KeyError:
                    frame_id = row_number
                annotations[frame_id].append(box(row))
            except (KeyError, ValueError):
                continue
    if not annotations:
        raise ValueError(f"Could not read usable boxes from {csv_path}")
    return annotations


def make_dirs() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    for split in ("train", "val"):
        (OUT / "images" / split).mkdir(parents=True)
        (OUT / "labels" / split).mkdir(parents=True)


def write_frame(frame, boxes, destination: Path) -> None:
    height, width = frame.shape[:2]
    labels: list[str] = []
    for x, y, w, h in boxes:
        x = max(0.0, x)
        y = max(0.0, y)
        w = min(w, width - x)
        h = min(h, height - y)
        if w < 4 or h < 4:
            continue
        labels.append(f"0 {(x + w / 2) / width:.6f} {(y + h / 2) / height:.6f} {w / width:.6f} {h / height:.6f}")
    if not labels:
        return
    cv2.imwrite(str(destination.with_suffix(".jpg")), frame, [cv2.IMWRITE_JPEG_QUALITY, 92])
    destination.with_suffix(".txt").write_text("\n".join(labels) + "\n", encoding="utf-8")


def convert(sample_every: int, seed: int) -> int:
    extract_zip_files()
    videos = sorted(path for path in RAW.rglob("*") if path.suffix.lower() in IMAGE_EXTENSIONS)
    if not videos:
        raise FileNotFoundError(f"Put the Kaggle ZIP or extracted files in {RAW}")
    make_dirs()
    random.seed(seed)
    total = 0
    for video in videos:
        annotations = read_annotations(find_matching_csv(video))
        frame_ids = sorted(frame for frame in annotations if frame % sample_every == 0)
        if not frame_ids:
            frame_ids = sorted(annotations)
        # These older AVI files occasionally expose fewer frames through the
        # installed decoder than are present in the CSV. Split only readable
        # frames; otherwise the validation directory can accidentally be empty.
        capture = cv2.VideoCapture(str(video))
        readable_ids: list[int] = []
        for frame_id in frame_ids:
            capture.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
            ok, _ = capture.read()
            if ok:
                readable_ids.append(frame_id)
        capture.release()
        capture = cv2.VideoCapture(str(video))
        cutoff = int(len(readable_ids) * 0.80)
        validation = set(readable_ids[cutoff:])
        for frame_id in frame_ids:
            capture.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
            ok, frame = capture.read()
            if not ok:
                continue
            split = "val" if frame_id in validation else "train"
            destination = OUT / "images" / split / f"{video.stem}_{frame_id:06d}"
            write_frame(frame, annotations[frame_id], destination)
            if destination.with_suffix(".jpg").exists():
                shutil.move(str(destination.with_suffix(".txt")), str(OUT / "labels" / split / destination.with_suffix(".txt").name))
                total += 1
        capture.release()
    print(f"Created {total} labelled frames in {OUT}")
    return total


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-every", type=int, default=8, help="Keep one labelled frame every N source frames.")
    parser.add_argument("--seed", type=int, default=42)
    options = parser.parse_args()
    convert(options.sample_every, options.seed)
