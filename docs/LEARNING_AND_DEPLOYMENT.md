# Current release: 2026-10-27.1
See [validation status](../Deliverables/Validation-Status.md) for sequential video analysis, individual-model adoption and verified limits.

# Learning from reviews and deployment
Implemented capability is separated from future work.

## Working correction-to-dataset loop
1. Review the entire report image. Correct false boxes and add missed damage. Save Confirmed (Assigned/Resolved reviewed records are also eligible).
2. Under Teach the next model, enter a capture group such as campus-run-01. Keep a road run, flight or video sequence in one group.
3. Assign train, validation or protected test. Confirm image-use permission and label review. Empty annotations require an explicit reviewed-negative checkbox.
4. Approve this example. Approval is bound to the saved report/image/annotation/status/update revision. Editing or reopening the review invalidates it; stale examples are excluded until approved again. Exact duplicate approved images are rejected. Capture groups cannot cross splits; export checks again.
5. Learning shows approved train/val/test counts. An administrator can export up to1000examples/512MiB as a local ZIP containing images, normalized YOLO labels, data.yaml and a provenance manifest (hash, original model, reviewer, revision, group and split). No live tokens, GPS or review notes are included. Images and reviewer identifiers in an export are still private workspace data.

Class order in exported labels:0D00,1D10,2D20,3D40,4OTHER. This differs from some friend's five-class training labels (OTHER3/D40 4); remap external data by class name before merging. Do not treat these indices as interchangeable.

## How the model actually learns
The app does not change weights when a review is saved or approved. Fine-tune a separate candidate on approved training examples plus representative prior training data. Use an absolute path to the exported data.yaml in your training environment; it resolves images relative to the extracted dataset. Create nonempty, protected validation/test groups before training or claiming metrics. Never mix adjacent frames across splits. Exact hashes are checked; near-duplicate/site leakage still requires a dataset audit.

Choose settings on validation data. Report per-class precision/recall, mAP50/mAP50-95, missed defects and laptop latency on independent test data. Import and activate the candidate only after evaluation; retain the old checkpoint for rollback. No retraining run using private reviewed reports was launched by this release, and no reviewed images were uploaded to Gemini/Antigravity/Colab.

## Working deployment
Windows launchers start a local Docker service and browser. Real reports remain on port8000 and the original persistent volume. Presentation data is separate on port18004 with a fixed public demo key and automatic connection. The real key remains private and has a one-click clipboard helper. A fresh stopped-service backup and rollback image precede the update.

## Further work, not current claims
Automated retraining/promotion, an independently evaluated ensemble, georeferenced drone/RTSP SDK ingest, hosted HTTPS deployment, push dispatch, and a signed clean-PC-tested Windows/mobile installer are not implemented/verified. Browser-playable dashcam/drone video files can be analyzed, but field performance on those views is unmeasured.
