# RPEE-Heads CNN integration notes

## Implemented interface
- HOG remains the default detector.
- Optional TorchScript adapter is selected with `RAILGUARD_DETECTOR=cnn`.
- The video sampling, API route and heuristic risk rules remain in place.
- API response includes `detector` to identify the selected backend.

## Not included
This branch does not download the RPEE-Heads dataset, train a CNN, or provide trained weights. It does not establish model accuracy or actual railway-track segmentation. The previously created synthetic CSV is not image training data.

## Checkpoint interface
The adapter expects a TorchScript module taking an RGB float tensor `[1,3,H,W]` scaled to `[0,1]` and returning `[N,6]` rows in pixel coordinates: `x1,y1,x2,y2,confidence,class_id`. Class ID 0 is treated as a head. Different model interfaces require a corresponding adapter change.

## Validation required
1. Verify dataset access, license and annotation format.
2. Split train/validation/test by scene or sequence to reduce leakage.
3. Train/export the model and document preprocessing and output semantics.
4. Evaluate on held-out scenes with detection metrics and inspect false positives/negatives.
5. Compare video outputs with annotated ground truth.
6. Calibrate camera-specific track zones separately; the bottom-18% band is only a placeholder.
7. Revisit risk thresholds because head counts and pedestrian counts have different semantics.
