# Current release: 2026-10-27.1
See [validation status](../Deliverables/Validation-Status.md) for sequential video analysis, individual-model adoption and verified limits.

# Live recognition and models

## What works
Iriun/USB/laptop cameras and browser-playable MP4/WebM files share a serial frame pipeline. Overview > Open camera starts analysis automatically. Live recognition > Start gives explicit source and quality controls. No Capture button is required for analysis.

The preview is sampled one frame at a time, with a one-second wait after each result. Balanced uses an input size up to640px; Detail uses the selected checkpoint's configured size (the leading friend models use800px). Actual frame dimensions and original-coordinate boxes stay aligned on the exact processed still. Frames are not automatically saved. Use this frame for a report is an explicit separate action.

Requests have a60-second browser deadline. Temporary errors retry automatically; three consecutive errors stop the loop with a clear message. Stop/navigation/hidden tab/disconnect release camera tracks and invalidate late work. Heavy work returns busy rather than overlapping inference.

## Confirmed RT-DETR fix
The installed RT-DETR postprocessor can return finite boxes across the image border. The previous adapter rejected the entire frame. This was reproduced on public Czech-Czech_000060.jpg (inference_ValueError with one outside-image box). The adapter now clips finite model coordinates to the image and drops zero-area boxes. Nonfinite/unknown/invalid outputs still fail. Strict human-annotation validation is unchanged.

The fix completed ten subsequent API checks: five public road images in both Detail800 and Balanced640. These are functional/timing diagnostics, not independent accuracy measurements. Memory improvements release the retained checkpoint training payload and predictor source/result tensors.

## 4K uploads
Report uploads now default to50MiB and25,000,000pixels. A24,893,576-byte3840x2160 PNG was accepted and retained at3840x2160 after metadata-stripping JPEG re-encoding. Source bytes/EXIF are not retained. The model still resizes internally to its configured640/800/etc input; a4K upload does not mean native4K inference or guaranteed small-defect accuracy.

## Model library
Settings accepts trusted .pt checkpoints or model ZIPs. Import never activates a model. Use model verifies SHA256, class names, loading and a synthetic forward pass before swapping. Failed activation retains the prior detector. The selected identifier persists across restart; the original baseline is retained for rollback.

Imported five-class friend models map index3Other_Corruption toOTHER and index4Pothole toD40. Four-class models map index3 toD40. Names are normalized explicitly; unknown/duplicate/missing classes are rejected. No positional guessing.

Each checkpoint can be700MiB; packages1600MiB; archives up to16models/100entries/1800MiB expanded. Restricted deserialization reduces unsupported serialized-code exposure but is not a sandbox for malicious files. Import only trusted checkpoints. One Uvicorn worker is required for the process-local runtime lock.

## Model voting
Open a saved report and select2-3distinct checkpoint hashes. The defaults are RT-DETR L, YOLO11s and YOLOv8m800 when present. Models run sequentially in separate90-second workers; tensor memory is released on worker exit. Existing active selection and saved boxes do not change. Live requests receive busy during a vote.

Same-class boxes are spatially matched atIoU0.5, with one vote per checkpoint per region. Two models require both; three require two. Unsupported OTHER classes abstain, but at least two capable models must agree. Coordinates are confidence-weighted means; displayed scores are means of detector scores, not calibrated correctness probabilities. Agreements are green and disagreements amber. If any model fails/times out, consensus is withheld rather than silently lowering the quorum. A user can explicitly copy consensus into the review draft, inspect it and save.

Voting may suppress real damage or amplify shared errors. No ensemble accuracy improvement has been measured. It is a frozen-image second opinion; all eight models do not run on every live frame.
