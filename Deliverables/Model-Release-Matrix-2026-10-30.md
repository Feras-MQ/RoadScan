# Model release and evidence matrix — 30 October 2026

**22 unique weights: 19 road detectors, one classifier, one COCO initializer and one DINOv2 backbone.** The new package contains four files, but its original/main model duplicates an existing SHA; only three weights are new. All requested publication permissions are recorded; permission is separate from establishing applicable upstream terms and complete covered source.

The baseline and DINOv2 mirrors are published; the stock initializer has an official upstream link. The remaining **19 weights** are preserved locally while their specific source/terms evidence is resolved. This is an evidence-completeness decision, not a finding that these team models are unlawful. Private inference does not require rerunning training.

## Read the columns correctly

- **Permission:** the owner's publication instruction; no ranking gate and no repeated blanket approval.
- **Source/terms:** notices and actual covered source mapping. The [AGPL text](https://raw.githubusercontent.com/ultralytics/ultralytics/v8.4.175/LICENSE) describes corresponding-source and distribution duties; [Ultralytics' policy](https://www.ultralytics.com/license) also addresses its trained models. A missing notebook, missing historical Git commit or missing repository-root license is not by itself a demonstrated redistribution prohibition. Confirm stock code or supply the actual modifications; do not invent a new license for third-party material.
- **Reproducibility/tests:** split leakage, missing evaluator/parent hash, unknown selection and missing field data constrain evidence claims. They are not automatically permission or licensing barriers. [Torchvision warns that pretrained weights may have their own terms](https://docs.pytorch.org/vision/stable/models.html); [DINOv2 identifies Apache-2.0 for its models](https://github.com/facebookresearch/dinov2/blob/main/MODEL_CARD.md).
- RT-DETR files here serialize Ultralytics classes and carry AGPL notices; the [original RT-DETR repository's Apache license](https://github.com/lyuwenyu/RT-DETR/blob/main/LICENSE) alone does not establish the terms of these particular checkpoints.

## Smallest remaining inputs

1. For the original trained YOLO/RT-DETR runs: the trainer can provide a compact run-to-source map stating stock package/version or actual patches, initial checkpoint source (or scratch), and terms for any additional covered team source. Existing embedded versions below are evidence already available; they need not be rediscovered. A historical notebook is not mandatory where the complete relevant source is otherwise identified.
2. For the three road fine-tunes: confirm the parent chain and whether the nine published files plus stock 8.4.175 contain all covered modifications. The nine-file team grant is already approved. Explain v1's manual selection separately for reproducibility; this is not another license request.
3. For ResNet18: identify scratch versus exact pretrained initializer and applicable checkpoint terms. A generic BSD label for the library does not answer that question.

No missing accuracy score, incomplete benchmark, expensive retraining, or new paid service is required just to use the locally tested models. The exact fresh-download acceptance operation remains separately stopped; its scope is documented in the [current audit](Submission-Audit-2026-10-30.md).

## Weight-by-weight record

The [machine-readable matrix](Model-Release-Matrix-2026-10-30.json) contains the same full identities and decisions. SHA-256 values below identify the original bytes; no weight has been renamed internally, edited, re-saved, or republished in this audit.

### 1. roadscan_baseline_best.pt

SHA-256: `2bb146ad53a3ddd149320aae3be67b2b1d50ccf0fdbc909edd749538055a2551`
Size: 5,536,234 bytes. Role: `road_detector`.

| Question | Evidence / decision |
|---|---|
| Permission | Approved by owner; no rank/top-five privacy hold. |
| Parent / original pretraining | Official yolo11n.pt; parent SHA256 0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1. |
| Available source | Published baseline packet: notebook, six preparation/training Python files, two configs and two dependency files; exact eleven-file grant applied. |
| Source / license evidence | AGPL-3.0 notice and approved scoped source grant distributed with source packet; no whole-app relicense. |
| Publication | PUBLISHED: anonymous download and exact SHA verified on 28 October; release still listed on 30 October. |
| Smallest missing input | None for the existing weight/source download. Fresh public-download-to-inference acceptance remains stopped; do not present it as passed. |
| Reproducibility gaps | Recorded baseline experiment exists; this audit does not rerun training or the US holdout. |
| Tests | Earlier isolated CPU inference recorded; fresh download-to-inference acceptance not completed. |

Recorded framework: 8.4.175.

[Download original weight](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/2bb146ad53a3-roadscan_baseline_best.pt).

Evidence: [source 1](https://github.com/Feras-MQ/RoadScan/releases/tag/model-resources-2026-10-28), [source 2](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/RoadScan-Baseline-Source-AGPL-3.0.zip).

### 2. road_damage_rtdetr_x_best_Epoch001_mAP50_95_0.00000.pt

SHA-256: `bda15131e5f68a3a010dcec312f343b9e54e90f4828efdb21a2f64fb342cc447`
Size: 540,036,156 bytes. Role: `road_detector`.

| Question | Evidence / decision |
|---|---|
| Permission | Approved by owner; no rank/top-five privacy hold. |
| Parent / original pretraining | Saved initializer filename candidate(s): rtdetr-x.pt; exact parent bytes not established. |
| Available source | Saved class map/configuration and embedded Ultralytics implementation/version evidence; exact run code or patch confirmation absent. |
| Source / license evidence | Embedded AGPL-3.0 notice; preserve it. Source completeness is unverified, not proof of infringement. |
| Publication | HOLD: asset source mapping has not been established. |
| Smallest missing input | Trainer confirmation identifying the recorded stock Ultralytics version and whether it was modified; provide any actual patches/covered custom code with existing terms. Identify the initializer source (or state trained from scratch). A historical notebook is not mandatory if an equivalent complete source description is available. |
| Reproducibility gaps | Exact data/split/selection lineage and independent evaluation remain unverified; these do not alone prohibit publication or private inference. |
| Tests | No new inference or accuracy test in this documentation audit. |

Recorded framework: 8.4.175.

Evidence: [source 1](detector-config-provenance-map.json), [source 2](public-model-inventory.json).

### 3. road_damage_rtdetr_x_final_best_Epoch050_mAP50_95_0.04830.pt

SHA-256: `edb35d3cf7b115d56a7bc96c6e4505c4a1da50ae1aecdf80742f49bae2a75a6d`
Size: 135,456,021 bytes. Role: `road_detector`.

| Question | Evidence / decision |
|---|---|
| Permission | Approved by owner; no rank/top-five privacy hold. |
| Parent / original pretraining | Saved initializer filename candidate(s): rtdetr-x.pt; exact parent bytes not established. |
| Available source | Saved class map/configuration and embedded Ultralytics implementation/version evidence; exact run code or patch confirmation absent. |
| Source / license evidence | Embedded AGPL-3.0 notice; preserve it. Source completeness is unverified, not proof of infringement. |
| Publication | HOLD: asset source mapping has not been established. |
| Smallest missing input | Trainer confirmation identifying the recorded stock Ultralytics version and whether it was modified; provide any actual patches/covered custom code with existing terms. Identify the initializer source (or state trained from scratch). A historical notebook is not mandatory if an equivalent complete source description is available. |
| Reproducibility gaps | Exact data/split/selection lineage and independent evaluation remain unverified; these do not alone prohibit publication or private inference. |
| Tests | No new inference or accuracy test in this documentation audit. |

Recorded framework: 8.4.175.

Evidence: [source 1](detector-config-provenance-map.json), [source 2](public-model-inventory.json).

### 4. road_damage_yolo11m_best_Epoch086_mAP50_95_0.21440.pt

SHA-256: `9e2a0484d6f4fc7938d7e5014673f080d6bb97f697b45e8676325db76131836a`
Size: 40,526,764 bytes. Role: `road_detector`.

| Question | Evidence / decision |
|---|---|
| Permission | Approved by owner; no rank/top-five privacy hold. |
| Parent / original pretraining | Saved initializer filename candidate(s): yolo11m.pt; exact parent bytes not established. |
| Available source | Saved class map/configuration and embedded Ultralytics implementation/version evidence; exact run code or patch confirmation absent. |
| Source / license evidence | Embedded AGPL-3.0 notice; preserve it. Source completeness is unverified, not proof of infringement. |
| Publication | HOLD: asset source mapping has not been established. |
| Smallest missing input | Trainer confirmation identifying the recorded stock Ultralytics version and whether it was modified; provide any actual patches/covered custom code with existing terms. Identify the initializer source (or state trained from scratch). A historical notebook is not mandatory if an equivalent complete source description is available. |
| Reproducibility gaps | Exact data/split/selection lineage and independent evaluation remain unverified; these do not alone prohibit publication or private inference. |
| Tests | No new inference or accuracy test in this documentation audit. |

Recorded framework: 8.4.175.

Evidence: [source 1](detector-config-provenance-map.json), [source 2](public-model-inventory.json).

### 5. road_damage_yolov8m_optimized_best_Epoch097_mAP50_95_0.21809.pt

SHA-256: `9a13443ad7a3f71c211059cc9b62e67e4157f7b49680d75a9ffca96742967e97`
Size: 52,041,426 bytes. Role: `road_detector`.

| Question | Evidence / decision |
|---|---|
| Permission | Approved by owner; no rank/top-five privacy hold. |
| Parent / original pretraining | Saved initializer filename candidate(s): yolov8m.pt; exact parent bytes not established. |
| Available source | Saved class map/configuration and embedded Ultralytics implementation/version evidence; exact run code or patch confirmation absent. |
| Source / license evidence | Embedded AGPL-3.0 notice; preserve it. Source completeness is unverified, not proof of infringement. |
| Publication | HOLD: asset source mapping has not been established. |
| Smallest missing input | Trainer confirmation identifying the recorded stock Ultralytics version and whether it was modified; provide any actual patches/covered custom code with existing terms. Identify the initializer source (or state trained from scratch). A historical notebook is not mandatory if an equivalent complete source description is available. |
| Reproducibility gaps | Exact data/split/selection lineage and independent evaluation remain unverified; these do not alone prohibit publication or private inference. |
| Tests | No new inference or accuracy test in this documentation audit. |

Recorded framework: 8.4.175.

Evidence: [source 1](detector-config-provenance-map.json), [source 2](public-model-inventory.json).

### 6. RTDETR_L_RDD2022_200E_800px_best_Epoch068_mAP50_95_0.31278.pt

SHA-256: `b636269a303539174ab208d125ab60de149fe832c4fda7aa4c25c8f109b45b60`
Size: 263,739,370 bytes. Role: `road_detector`.

| Question | Evidence / decision |
|---|---|
| Permission | Approved by owner; no rank/top-five privacy hold. |
| Parent / original pretraining | Saved initializer filename candidate(s): rtdetr-l.pt; exact parent bytes not established. |
| Available source | Saved class map/configuration and embedded Ultralytics implementation/version evidence; exact run code or patch confirmation absent. |
| Source / license evidence | Embedded AGPL-3.0 notice; preserve it. Source completeness is unverified, not proof of infringement. |
| Publication | HOLD: asset source mapping has not been established. |
| Smallest missing input | Trainer confirmation identifying the recorded stock Ultralytics version and whether it was modified; provide any actual patches/covered custom code with existing terms. Identify the initializer source (or state trained from scratch). A historical notebook is not mandatory if an equivalent complete source description is available. |
| Reproducibility gaps | Exact data/split/selection lineage and independent evaluation remain unverified; these do not alone prohibit publication or private inference. |
| Tests | No new inference or accuracy test in this documentation audit. |

Recorded framework: 8.4.177.

Evidence: [source 1](detector-config-provenance-map.json), [source 2](public-model-inventory.json).

### 7. setup_benchmark_best_Epoch001_mAP50_95_0.00001.pt

SHA-256: `11602fd792d5f68427d254c9613a60ca3e077bcf42ddc4dc46c6ea1fad17c698`
Size: 135,449,685 bytes. Role: `road_detector`.

| Question | Evidence / decision |
|---|---|
| Permission | Approved by owner; no rank/top-five privacy hold. |
| Parent / original pretraining | Saved initializer filename candidate(s): rtdetr-x.pt; exact parent bytes not established. |
| Available source | Saved class map/configuration and embedded Ultralytics implementation/version evidence; exact run code or patch confirmation absent. |
| Source / license evidence | Embedded AGPL-3.0 notice; preserve it. Source completeness is unverified, not proof of infringement. |
| Publication | HOLD: asset source mapping has not been established. |
| Smallest missing input | Trainer confirmation identifying the recorded stock Ultralytics version and whether it was modified; provide any actual patches/covered custom code with existing terms. Identify the initializer source (or state trained from scratch). A historical notebook is not mandatory if an equivalent complete source description is available. |
| Reproducibility gaps | Exact data/split/selection lineage and independent evaluation remain unverified; these do not alone prohibit publication or private inference. |
| Tests | No new inference or accuracy test in this documentation audit. |

Recorded framework: 8.4.175.

Evidence: [source 1](detector-config-provenance-map.json), [source 2](public-model-inventory.json).

### 8. YOLO11s_RDD2022_200E_800px_best_Epoch085_mAP50_95_0.34684.pt

SHA-256: `e1937609619f0172b0765d676cd0b8167adbda979cb4d3cabeaf61e6395b7758`
Size: 19,219,610 bytes. Role: `road_detector`.

| Question | Evidence / decision |
|---|---|
| Permission | Approved by owner; no rank/top-five privacy hold. |
| Parent / original pretraining | Saved initializer filename candidate(s): yolo11s.pt; exact parent bytes not established. |
| Available source | Saved class map/configuration and embedded Ultralytics implementation/version evidence; exact run code or patch confirmation absent. |
| Source / license evidence | Embedded AGPL-3.0 notice; preserve it. Source completeness is unverified, not proof of infringement. |
| Publication | HOLD: asset source mapping has not been established. |
| Smallest missing input | Trainer confirmation identifying the recorded stock Ultralytics version and whether it was modified; provide any actual patches/covered custom code with existing terms. Identify the initializer source (or state trained from scratch). A historical notebook is not mandatory if an equivalent complete source description is available. |
| Reproducibility gaps | Exact data/split/selection lineage and independent evaluation remain unverified; these do not alone prohibit publication or private inference. |
| Tests | No new inference or accuracy test in this documentation audit. |

Recorded framework: 8.4.178.

Evidence: [source 1](detector-config-provenance-map.json), [source 2](public-model-inventory.json).

### 9. YOLOv8m_RDD2022_150E_800px_best_Epoch021_mAP50_95_0.30855.pt

SHA-256: `4e14d23d45da6d74504f24632d3f58b447ed6310caf1129b141c736f77e556c1`
Size: 103,884,827 bytes. Role: `road_detector`.

| Question | Evidence / decision |
|---|---|
| Permission | Approved by owner; no rank/top-five privacy hold. |
| Parent / original pretraining | No exact initializer identified in the inspected record. |
| Available source | Saved class map/configuration and embedded Ultralytics implementation/version evidence; exact run code or patch confirmation absent. |
| Source / license evidence | Embedded AGPL-3.0 notice; preserve it. Source completeness is unverified, not proof of infringement. |
| Publication | HOLD: asset source mapping has not been established. |
| Smallest missing input | Trainer confirmation identifying the recorded stock Ultralytics version and whether it was modified; provide any actual patches/covered custom code with existing terms. Identify the initializer source (or state trained from scratch). A historical notebook is not mandatory if an equivalent complete source description is available. |
| Reproducibility gaps | Exact data/split/selection lineage and independent evaluation remain unverified; these do not alone prohibit publication or private inference. |
| Tests | No new inference or accuracy test in this documentation audit. |

Recorded framework: 8.4.175.

Evidence: [source 1](detector-config-provenance-map.json), [source 2](public-model-inventory.json).

### 10. yolo11n.pt

SHA-256: `0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1`
Size: 5,613,764 bytes. Role: `stock_coco`.

| Question | Evidence / decision |
|---|---|
| Permission | Approved by owner; no rank/top-five privacy hold. |
| Parent / original pretraining | Official Ultralytics COCO-pretrained YOLO11n initializer; not team-trained. |
| Available source | Official Ultralytics implementation and upstream asset; source/notices remain upstream. |
| Source / license evidence | Upstream Ultralytics terms; no new license is assigned. |
| Publication | UPSTREAM DOWNLOAD: exact file/hash previously verified; no RoadScan mirror. |
| Smallest missing input | None for the official link. This is not a road-damage model. |
| Reproducibility gaps | Does not reproduce RoadScan training and cannot replace a trained road detector. |
| Tests | No new inference or accuracy test in this documentation audit. |

[Download original weight](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt).

Evidence: [source 1](https://github.com/ultralytics/ultralytics), [source 2](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt).

### 11. e2_yolo26s_640.pt

SHA-256: `31b518ed36ec022fcadb0768268d4b6686a4c327bec3a9cd4fe5fc722ee4cc83`
Size: 20,318,592 bytes. Role: `road_detector`.

| Question | Evidence / decision |
|---|---|
| Permission | Approved by owner; no rank/top-five privacy hold. |
| Parent / original pretraining | Saved initializer filename candidate(s): yolo26s.pt; exact parent bytes not established. |
| Available source | Saved class map/configuration and embedded Ultralytics implementation/version evidence; exact run code or patch confirmation absent. |
| Source / license evidence | Embedded AGPL-3.0 notice; preserve it. Source completeness is unverified, not proof of infringement. |
| Publication | HOLD: asset source mapping has not been established. |
| Smallest missing input | Trainer confirmation identifying the recorded stock Ultralytics version and whether it was modified; provide any actual patches/covered custom code with existing terms. Identify the initializer source (or state trained from scratch). A historical notebook is not mandatory if an equivalent complete source description is available. |
| Reproducibility gaps | Exact data/split/selection lineage and independent evaluation remain unverified; these do not alone prohibit publication or private inference. |
| Tests | No new inference or accuracy test in this documentation audit. |

Recorded framework: 8.4.177.

Evidence: [source 1](detector-config-provenance-map.json), [source 2](public-model-inventory.json).

### 12. data_yolo26s_640_clean_labels.pt

SHA-256: `1bb6724ee2d01cf0f64c81ae8b6845c70ba06776d51b189f0f3052f880e96543`
Size: 20,318,592 bytes. Role: `road_detector`.

| Question | Evidence / decision |
|---|---|
| Permission | Approved by owner; no rank/top-five privacy hold. |
| Parent / original pretraining | Saved initializer filename candidate(s): yolo26s.pt; exact parent bytes not established. |
| Available source | Saved class map/configuration and embedded Ultralytics implementation/version evidence; exact run code or patch confirmation absent. |
| Source / license evidence | Embedded AGPL-3.0 notice; preserve it. Source completeness is unverified, not proof of infringement. |
| Publication | HOLD: asset source mapping has not been established. |
| Smallest missing input | Trainer confirmation identifying the recorded stock Ultralytics version and whether it was modified; provide any actual patches/covered custom code with existing terms. Identify the initializer source (or state trained from scratch). A historical notebook is not mandatory if an equivalent complete source description is available. |
| Reproducibility gaps | Exact data/split/selection lineage and independent evaluation remain unverified; these do not alone prohibit publication or private inference. |
| Tests | No new inference or accuracy test in this documentation audit. |

Recorded framework: 8.4.177.

Evidence: [source 1](detector-config-provenance-map.json), [source 2](public-model-inventory.json).

### 13. main_yolo26s_1024.pt

SHA-256: `9f940caa92229f503eef1171010c13ee8fd74d7b69300e959357d6a8d14be434`
Size: 20,414,080 bytes. Role: `road_detector`.

| Question | Evidence / decision |
|---|---|
| Permission | Approved by owner; no rank/top-five privacy hold. |
| Parent / original pretraining | Saved initializer filename candidate(s): yolo26s.pt; exact parent bytes not established. |
| Available source | Saved class map/configuration and embedded Ultralytics implementation/version evidence; exact run code or patch confirmation absent. Supplied again byte-identically as the original in the new road package; nine-file fine-tune grant does not cover missing original-main source. |
| Source / license evidence | Embedded AGPL-3.0 notice; preserve it. Source completeness is unverified, not proof of infringement. |
| Publication | HOLD: asset source mapping has not been established. |
| Smallest missing input | Trainer confirmation identifying the recorded stock Ultralytics version and whether it was modified; provide any actual patches/covered custom code with existing terms. Identify the initializer source (or state trained from scratch). A historical notebook is not mandatory if an equivalent complete source description is available. |
| Reproducibility gaps | Exact data/split/selection lineage and independent evaluation remain unverified; these do not alone prohibit publication or private inference. Saved epoch is -1; original main mixed-data manifest remains absent. |
| Tests | 29 October: restricted loader plus actual CPU inference at 1024 on one synthetic and one road image completed. 30 October: selected main model verified unchanged. Compatibility only; no accuracy measurement. |

Recorded framework: 8.4.177.

Exact duplicate alias: `1_original_yolo26s_1024.pt`; not an additional model.

Evidence: [source 1](detector-config-provenance-map.json), [source 2](public-model-inventory.json).

### 14. e2_yolo26n_640.pt

SHA-256: `3be62681e3ecc306fd4fbbbcbd40f805fcdd092d03cd57373695ca0453b1aaf8`
Size: 5,463,296 bytes. Role: `road_detector`.

| Question | Evidence / decision |
|---|---|
| Permission | Approved by owner; no rank/top-five privacy hold. |
| Parent / original pretraining | Saved initializer filename candidate(s): yolo26n.pt; exact parent bytes not established. |
| Available source | Saved class map/configuration and embedded Ultralytics implementation/version evidence; exact run code or patch confirmation absent. |
| Source / license evidence | Embedded AGPL-3.0 notice; preserve it. Source completeness is unverified, not proof of infringement. |
| Publication | HOLD: asset source mapping has not been established. |
| Smallest missing input | Trainer confirmation identifying the recorded stock Ultralytics version and whether it was modified; provide any actual patches/covered custom code with existing terms. Identify the initializer source (or state trained from scratch). A historical notebook is not mandatory if an equivalent complete source description is available. |
| Reproducibility gaps | Exact data/split/selection lineage and independent evaluation remain unverified; these do not alone prohibit publication or private inference. |
| Tests | No new inference or accuracy test in this documentation audit. |

Recorded framework: 8.4.177.

Evidence: [source 1](detector-config-provenance-map.json), [source 2](public-model-inventory.json).

### 15. e3_yolo26s_640_no_augmentation.pt

SHA-256: `3ef405bf22a9324c1f8d43537e21e454a9b4df82cd08f7cb9a09d7d80d1f6edf`
Size: 20,318,592 bytes. Role: `road_detector`.

| Question | Evidence / decision |
|---|---|
| Permission | Approved by owner; no rank/top-five privacy hold. |
| Parent / original pretraining | Saved initializer filename candidate(s): yolo26s.pt; exact parent bytes not established. |
| Available source | Saved class map/configuration and embedded Ultralytics implementation/version evidence; exact run code or patch confirmation absent. |
| Source / license evidence | Embedded AGPL-3.0 notice; preserve it. Source completeness is unverified, not proof of infringement. |
| Publication | HOLD: asset source mapping has not been established. |
| Smallest missing input | Trainer confirmation identifying the recorded stock Ultralytics version and whether it was modified; provide any actual patches/covered custom code with existing terms. Identify the initializer source (or state trained from scratch). A historical notebook is not mandatory if an equivalent complete source description is available. |
| Reproducibility gaps | Exact data/split/selection lineage and independent evaluation remain unverified; these do not alone prohibit publication or private inference. |
| Tests | No new inference or accuracy test in this documentation audit. |

Recorded framework: 8.4.177.

Evidence: [source 1](detector-config-provenance-map.json), [source 2](public-model-inventory.json).

### 16. e3_yolo26s_640_vertical_flip.pt

SHA-256: `63d2099e766f5a6ee8bcc7bd915487b99ec03a7da33940c279e844954bf91e08`
Size: 20,318,720 bytes. Role: `road_detector`.

| Question | Evidence / decision |
|---|---|
| Permission | Approved by owner; no rank/top-five privacy hold. |
| Parent / original pretraining | No exact initializer identified in the inspected record. |
| Available source | Saved class map/configuration and embedded Ultralytics implementation/version evidence; exact run code or patch confirmation absent. |
| Source / license evidence | Embedded AGPL-3.0 notice; preserve it. Source completeness is unverified, not proof of infringement. |
| Publication | HOLD: asset source mapping has not been established. |
| Smallest missing input | Trainer confirmation identifying the recorded stock Ultralytics version and whether it was modified; provide any actual patches/covered custom code with existing terms. Identify the initializer source (or state trained from scratch). A historical notebook is not mandatory if an equivalent complete source description is available. |
| Reproducibility gaps | Exact data/split/selection lineage and independent evaluation remain unverified; these do not alone prohibit publication or private inference. |
| Tests | No new inference or accuracy test in this documentation audit. |

Recorded framework: 8.4.177.

Evidence: [source 1](detector-config-provenance-map.json), [source 2](public-model-inventory.json).

### 17. e4_yolo26s_640_without_India.pt

SHA-256: `fa148e7109aad2f30075305bc46e53c8c24fbc6c29ed7167436a30de2acb16bb`
Size: 20,318,592 bytes. Role: `road_detector`.

| Question | Evidence / decision |
|---|---|
| Permission | Approved by owner; no rank/top-five privacy hold. |
| Parent / original pretraining | Saved initializer filename candidate(s): yolo26s.pt; exact parent bytes not established. |
| Available source | Saved class map/configuration and embedded Ultralytics implementation/version evidence; exact run code or patch confirmation absent. |
| Source / license evidence | Embedded AGPL-3.0 notice; preserve it. Source completeness is unverified, not proof of infringement. |
| Publication | HOLD: asset source mapping has not been established. |
| Smallest missing input | Trainer confirmation identifying the recorded stock Ultralytics version and whether it was modified; provide any actual patches/covered custom code with existing terms. Identify the initializer source (or state trained from scratch). A historical notebook is not mandatory if an equivalent complete source description is available. |
| Reproducibility gaps | Exact data/split/selection lineage and independent evaluation remain unverified; these do not alone prohibit publication or private inference. |
| Tests | No new inference or accuracy test in this documentation audit. |

Recorded framework: 8.4.177.

Evidence: [source 1](detector-config-provenance-map.json), [source 2](public-model-inventory.json).

### 18. baseline_resnet18.pt

SHA-256: `267c1eefc78dedf7fe13e9d2e899695b7f5d1edefa98ee7115356d2c6d47b21c`
Size: 44,793,483 bytes. Role: `classifier`.

| Question | Evidence / decision |
|---|---|
| Permission | Approved by owner; no rank/top-five privacy hold. |
| Parent / original pretraining | ResNet18 architecture is identified; exact starting checkpoint, source and terms are not established. |
| Available source | Replacement classifier implementation exists in this repository; it is not evidence of the original training source. |
| Source / license evidence | Torchvision code license does not establish this checkpoint's weight terms; no explicit artifact license proven here. |
| Publication | HOLD: initializer/checkpoint terms are not established. |
| Smallest missing input | Trainer: state scratch or exact pretrained weight ID/URL, identify any third-party checkpoint terms and any own additions. Original notebook absence alone is not a prohibition. |
| Reproducibility gaps | Original training recipe and split lineage are missing; replacement synthetic tests are not reproduction of this weight. |
| Tests | No new inference or accuracy test in this documentation audit. |

Evidence: [source 1](Team-Models-and-Results.md), [source 2](https://docs.pytorch.org/vision/stable/models.html).

### 19. dinov2_vits14_pretrain.pth

SHA-256: `b938bf1bc15cd2ec0feacfe3a1bb553fe8ea9ca46a7e1d8d00217f29aef60cd9`
Size: 88,283,115 bytes. Role: `embedding`.

| Question | Evidence / decision |
|---|---|
| Permission | Approved by owner; no rank/top-five privacy hold. |
| Parent / original pretraining | Unmodified official Meta DINOv2 ViT-S/14 pretrained backbone. |
| Available source | Official DINOv2 source/model card; published Apache license and provenance packet. |
| Source / license evidence | Apache-2.0 model/source evidence; notices shipped with the mirror. |
| Publication | PUBLISHED: anonymous download and exact SHA verified on 28 October; release still listed on 30 October. |
| Smallest missing input | None for redistribution of the unchanged published asset. Real duplicate-pair calibration is a separate task. |
| Reproducibility gaps | Does not detect boxes. Real-pair retrieval and threshold validation remain unmeasured. |
| Tests | No new inference or accuracy test in this documentation audit. |

[Download original weight](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/b938bf1bc15c-dinov2_vits14_pretrain.pth).

Evidence: [source 1](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/DINOv2-license-provenance.zip), [source 2](https://github.com/facebookresearch/dinov2/blob/main/MODEL_CARD.md).

### 20. 2_road_v1_yolo26s_1024_RECOMMENDED.pt

SHA-256: `78f5e2afb82d5145f30de9957cb51f167241e377ed0b5775f71be1c5e80ac87d`
Size: 20,444,878 bytes. Role: `road_detector`.

| Question | Evidence / decision |
|---|---|
| Permission | Owner authorized inclusion/publication of eligible new team models; no extra rank/selection approval required. |
| Parent / original pretraining | main_yolo26s_1024.pt (main lineage reported); saved filename supports lineage but does not cryptographically bind the historical parent. These are team fine-tunes, not new third-party pretrained models. |
| Available source | Nine sanitized team source/config files published under the approved AGPL-3.0-only grant; notebook pins stock Ultralytics 8.4.175. Historical v1 script and args retained. |
| Source / license evidence | Embedded AGPL-3.0 notice and approved nine-file source grant. Exact parent-main/custom-implementation source mapping remains unverified; no new permission question is inferred. |
| Publication | HOLD: parent/source mapping requires confirmation; not held for accuracy, missing historical notebook, or model ranking. |
| Smallest missing input | Trainer: confirm stock 8.4.175 or provide actual patches; identify the parent used and link its covered source/terms (main 9f940caa9222, via v1 for v2b if confirmed). Supply any missing covered preparation/training modifications or confirm the published nine files are complete for this fine-tune. |
| Reproducibility gaps | Supplied v1 selection rule rejects all recorded epochs; actual manual selection/export explanation missing. Road set was used in selection, shares video sequences across partitions, and big-test evaluator is absent; supplied scores are not independent held-out accuracy. |
| Tests | 29 October: restricted loading and actual CPU1024 inference on one synthetic and one road image passed. 30 October: distinct experimental choice visible in model library; not activated. No accuracy or sustained-speed claim. |

Recorded framework: 8.4.175.

Evidence: [source 1](../model_sources/road-finetunes-2026-10-29/NOTICE.md), [source 2](../model_sources/road-finetunes-2026-10-29/Source-Manifest.json), [source 3](../model_sources/road-finetunes-2026-10-29/Model-Metadata.json), [source 4](../model_sources/road-finetunes-2026-10-29/README.md).

### 21. 3_road_A_yolo26s_1024.pt

SHA-256: `00794102e39e621f1268e31f43b3743daae17309b5eaf90feef1077f0bf0991b`
Size: 20,446,971 bytes. Role: `road_detector`.

| Question | Evidence / decision |
|---|---|
| Permission | Owner authorized inclusion/publication of eligible new team models; no extra rank/selection approval required. |
| Parent / original pretraining | main_yolo26s_1024.pt (main lineage reported); saved filename supports lineage but does not cryptographically bind the historical parent. These are team fine-tunes, not new third-party pretrained models. |
| Available source | Nine sanitized team source/config files published under the approved AGPL-3.0-only grant; notebook pins stock Ultralytics 8.4.175. Current notebook/trainer and saved run A args are available. |
| Source / license evidence | Embedded AGPL-3.0 notice and approved nine-file source grant. Exact parent-main/custom-implementation source mapping remains unverified; no new permission question is inferred. |
| Publication | HOLD: parent/source mapping requires confirmation; not held for accuracy, missing historical notebook, or model ranking. |
| Smallest missing input | Trainer: confirm stock 8.4.175 or provide actual patches; identify the parent used and link its covered source/terms (main 9f940caa9222, via v1 for v2b if confirmed). Supply any missing covered preparation/training modifications or confirm the published nine files are complete for this fine-tune. |
| Reproducibility gaps | Saved selection rule is consistent with epoch 4; exact historical parent hash unverified. Road set was used in selection, shares video sequences across partitions, and big-test evaluator is absent; supplied scores are not independent held-out accuracy. |
| Tests | 29 October: restricted loading and actual CPU1024 inference on one synthetic and one road image passed. 30 October: distinct experimental choice visible in model library; not activated. No accuracy or sustained-speed claim. |

Recorded framework: 8.4.175.

Evidence: [source 1](../model_sources/road-finetunes-2026-10-29/NOTICE.md), [source 2](../model_sources/road-finetunes-2026-10-29/Source-Manifest.json), [source 3](../model_sources/road-finetunes-2026-10-29/Model-Metadata.json), [source 4](../model_sources/road-finetunes-2026-10-29/README.md).

### 22. 4_road_v2b_yolo26s_1024.pt

SHA-256: `0caef4521c82a944cfe4b6e5022914eeabab9c69864967db17a9915f4fdc7500`
Size: 20,447,626 bytes. Role: `road_detector`.

| Question | Evidence / decision |
|---|---|
| Permission | Owner authorized inclusion/publication of eligible new team models; no extra rank/selection approval required. |
| Parent / original pretraining | main_yolo26s_1024_road.pt (v1 lineage reported); saved filename supports lineage but does not cryptographically bind the historical parent. These are team fine-tunes, not new third-party pretrained models. |
| Available source | Nine sanitized team source/config files published under the approved AGPL-3.0-only grant; notebook pins stock Ultralytics 8.4.175. Current notebook/trainer and saved run B args are available. |
| Source / license evidence | Embedded AGPL-3.0 notice and approved nine-file source grant. Exact parent-main/custom-implementation source mapping remains unverified; no new permission question is inferred. |
| Publication | HOLD: parent/source mapping requires confirmation; not held for accuracy, missing historical notebook, or model ranking. |
| Smallest missing input | Trainer: confirm stock 8.4.175 or provide actual patches; identify the parent used and link its covered source/terms (main 9f940caa9222, via v1 for v2b if confirmed). Supply any missing covered preparation/training modifications or confirm the published nine files are complete for this fine-tune. |
| Reproducibility gaps | Saved selection rule is consistent with epoch 3; exact historical parent hash unverified. Road set was used in selection, shares video sequences across partitions, and big-test evaluator is absent; supplied scores are not independent held-out accuracy. |
| Tests | 29 October: restricted loading and actual CPU1024 inference on one synthetic and one road image passed. 30 October: distinct experimental choice visible in model library; not activated. No accuracy or sustained-speed claim. |

Recorded framework: 8.4.175.

Evidence: [source 1](../model_sources/road-finetunes-2026-10-29/NOTICE.md), [source 2](../model_sources/road-finetunes-2026-10-29/Source-Manifest.json), [source 3](../model_sources/road-finetunes-2026-10-29/Model-Metadata.json), [source 4](../model_sources/road-finetunes-2026-10-29/README.md).
