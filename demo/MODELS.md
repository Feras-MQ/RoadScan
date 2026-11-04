# Demo models

The public workflow demo uses generated images with no prefilled boxes; you can add practice annotations. It can be explored without a detector. To run actual inference on your own inputs, first enable the [optional detector build](README.md#optional-real-inference), then download a published detector below and import it through the app's model library. Weights are separate release downloads and are not included in a repository ZIP.

The laptop catalog contained **nine models** at inspection: seven are already published and two have metadata only. The laptop had **Road v1** selected; Main produced most of the prepared showcase predictions. These are observations of that laptop state, not accuracy recommendations.

For the smallest download in this catalog, start with the **original YOLO11n baseline (5.5 MB)**. A local CPU timing check is recorded in [VERIFICATION.md](VERIFICATION.md); it does not establish accuracy or speed on another computer. You can switch to Main later.

| Model | SHA-256 prefix | Download |
| --- | --- | --- |
| Main YOLO26s (1024) | `9f940caa9222` | [Release asset](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/9f940caa9222-main_yolo26s_1024.pt) |
| Road v2b YOLO26s (1024, experimental) | `0caef4521c82` | [Release asset](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/0caef4521c82-main_yolo26s_1024_road_v2b.pt) |
| YOLO26n (640, size experiment) | `3be62681e3ec` | [Release asset](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/3be62681e3ec-e2_yolo26n_640.pt) |
| YOLO11s (800, RDD2022) | `e1937609619f` | Unavailable: source confirmation pending |
| Road v1 YOLO26s (1024, experimental) | `78f5e2afb82d` | [Release asset](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/78f5e2afb82d-main_yolo26s_1024_road.pt) |
| Road A YOLO26s (1024, experimental) | `00794102e39e` | [Release asset](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/00794102e39e-main_yolo26s_1024_road_v2.pt) |
| Original YOLO11n baseline (640) | `2bb146ad53a3` | [Release asset](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/2bb146ad53a3-roadscan_baseline_best.pt) |
| YOLO26s (640, size experiment) | `31b518ed36ec` | [Release asset](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/31b518ed36ec-e2_yolo26s_640.pt) |
| RT-DETR L (800, RDD2022) | `b636269a3035` | Unavailable: source confirmation pending |

Full SHA-256 values and byte sizes are in [laptop-snapshot.json](laptop-snapshot.json). Verify the downloaded file before importing it. For example, in PowerShell:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath ./downloaded-model.pt
```

For YOLO11s and RT-DETR L, the existing public inventory requires the original trainer to confirm that the recorded stock package/version was unmodified, or to supply the actual modifications and terms. Their binaries are not published by this demo update.

The release weights retain their existing asset-specific notices and source links. See the [model guide](../Deliverables/Models.md), [public inventory](../Deliverables/public-model-inventory.json), and [model release](https://github.com/Feras-MQ/RoadScan/releases/tag/model-resources-2026-10-28). No new license is assigned to the app or the model files here.

This is inspection metadata only. The original laptop database, photos, video, screenshots, caches and backups remain local. The public seed is independently generated and does not reproduce the original image predictions. Detector inference and model accuracy were not rerun as part of this metadata comparison.
