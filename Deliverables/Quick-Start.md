# RoadScan quick start

1. Install Docker Desktop and use Linux containers.
2. Download this repository and follow [Quick start — Windows](../README.md#quick-start--windows); it contains the tested setup commands.
3. Open the local address shown by the launcher and use your locally generated token.
4. Import a trusted, compatible checkpoint in **Settings → Your model library**, select **Use model**, and confirm **Active**; see [model availability](Models.md).
5. Analyze a road image, open the saved report, review the boxes and save your decision.

The source download requires a road-trained model for detection. The [published baseline and manual import steps](Inference-and-Reproducibility.md) are available; DINOv2 and stock COCO resources serve other tasks. No retraining or paid inference API is required once a compatible road checkpoint is installed. Fresh download-to-inference acceptance remains unverified; see the [current audit](Submission-Audit-2026-10-30.md).

For Iriun/USB, choose **Live recognition → Camera → Start**. For an uploaded video, choose **Analyze every frame**; processing can take longer than playback. Human corrections are saved for an approved training export; they do not instantly update the active model.

Keep the Docker data volume and `.env` when restarting. [Setup on another computer](Run-On-Another-Computer.md) also covers the separately supplied Ready-To-Run bundle.
