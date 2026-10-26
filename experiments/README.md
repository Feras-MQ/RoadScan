# Reproducible experiment contracts — no results claimed

Data prerequisites: verify RDD2022 source, license and annotations independently before any download. Store `data/manifest.csv` with `image_path,labels_path,country,sequence_group,split,location_source,privacy_status`. Do not train/tune on 40–80 local test photos. Group sequence IDs in one split, check cross-split near duplicates, reserve one country entirely for E4 held-out evaluation. Threshold/model selection uses validation only.

E1: multilabel image classifier baseline versus four-class detector; compare image-level metrics separately from localization mAP. E2: detector nano/small or 640/960; record CPU latency. E3: realistic horizontal flip/HSV versus mosaic settings; no unmotivated vertical flips. E4: held-out country and local final test as separate tables. E5: DCT pHash, ImageNet ResNet features, DINOv2-small crops; validation-only similarity threshold, pair labels and Recall@1/5. Current app's dHash is a *separate unvalidated local placeholder*, not E5 evidence.

Use `configs/experiments.yaml` as proposed run configurations; training commands below require an independently installed and license-reviewed Ultralytics package and locally prepared YAML manifests, and do NOT run as part of the MVP:
```
yolo detect train data=configs/rdd2022.yaml model=PATH_TO_LICENSED_NANO_CHECKPOINT imgsz=640 epochs=50 project=results name=e2_nano
 yolo detect val model=results/e2_nano/weights/best.pt data=configs/rdd2022.yaml split=val
```
The classifier and embedding experiments need team-authored model training/evaluation scripts; these are not implemented. The YAML configuration is a planning artifact, not a claim that experiments are runnable end to end.

Result template columns: `experiment,run_id,split,country,model_version,hardware,images,map50,map50_95,ap_D00,ap_D10,ap_D20,ap_D40,precision,recall,confusion_matrix_file,f1_confidence_curve_file,dup_recall1,dup_recall5,dup_threshold_precision,dup_threshold_recall,roc_file,cpu_inference_ms,e2e_ms,notes`. Blank cells mean **not measured**. Report errors, confidence intervals when feasible, and sample sizes. For priority sensitivity change each draft weight by ±20% individually, renormalize all weights to sum 1, and count changed ranks on a *real validation* report set; never use synthetic examples as evidence.

Pipeline smoke test: `pytest -q tests/test_pipeline.py`. Synthetic gray image verifies upload/persistence/manual review only; it cannot demonstrate detector performance.
