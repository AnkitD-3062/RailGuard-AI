# Occlusion-aware training

## Why CrowdHuman

CrowdHuman is specifically designed for dense crowds and partial pedestrian
occlusion. It supplies visible-body (`vbox`) labels, which are appropriate when
one passenger stands partly behind another.

## Prepare data

1. From a normal Windows PowerShell, run the included downloader. It requires
   about 11 GB for source archives, plus extra disk space while extracting:

```powershell
.\training\download_crowdhuman.ps1
```

It resumes interrupted downloads and verifies each file's SHA-256 checksum.
The mirror preserves the CrowdHuman CC-BY-NC-4.0 educational/non-commercial
licence; do not commit or redistribute the downloaded images.

2. Convert to YOLO labels:

```powershell
python training/convert_crowdhuman.py `
  --raw-dir datasets/crowdhuman_raw `
  --train-annotations datasets/crowdhuman_raw/annotation_train.odgt `
  --val-annotations datasets/crowdhuman_raw/annotation_val.odgt
```

## Fine-tune

To run download, conversion, and training in one command after creating
`.venv`, use:

```powershell
.\training\train_all.ps1
```

Or run the training step separately:

```powershell
python training/train.py --epochs 80 --imgsz 960 --device 0
```

The best checkpoint is normally at
`runs/railguard/crowdhuman-yolo11s/weights/best.pt`. Copy it to
`models/railguard-crowdhuman.pt`; the web application will choose it
automatically. Use `yolo11n.pt` instead of `yolo11s.pt` if the 6 GB GPU runs
out of memory.

## Measure improvement

Compare the original COCO model and the fine-tuned model on a held-out set of
authorised station images. Report precision, recall, mAP50-95, and false
positives. Do not claim a percentage improvement until this validation is run.

## Limits

No detector can identify a fully invisible person. Fine-tuning helps only when
part of the person remains visible. A deployment also needs authorised local
camera footage, camera-specific track polygons, and human review of alarms.
