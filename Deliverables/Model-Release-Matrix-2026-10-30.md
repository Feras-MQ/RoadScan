# Model release and evidence matrix — updated 31 October 2026

**22 verified local weight identities: 19 detectors, one classifier, one stock COCO initializer and one DINOv2 backbone.** Twelve weights are mirrored publicly (eleven road detectors and DINOv2), and the stock initializer has an official upstream link; nine are held individually. The four-file new package adds three unique hashes because its original duplicates Main. Two newly mentioned checkpoints were not found and are not silently counted as verified models.

## What changed

All 17 located files in the new trainer inventory matched both the supplied MD5 and existing SHA256. Ten newly eligible models were published unchanged with verified official source archives, existing notices, approved fine-tune source, provenance and checksums; all 13 new release assets were fetched anonymously and hash-checked. See [trainer evidence and per-asset caveats](Trainer-Provenance-2026-10-31.md).

Publication permission, applicable terms, and reproducibility are separate. Trainer confirmation of stock pip code resolves the previously missing source mapping for the ten releases; a missing notebook, historic parent hash, benchmark or evaluator is not automatically a publication prohibition. The older-machine caveat remains specific to those assets. No new blanket license or whole-app grant has been invented. See the [AGPL text](https://raw.githubusercontent.com/ultralytics/ultralytics/v8.4.175/LICENSE), [Ultralytics policy](https://www.ultralytics.com/license), [Torchvision model terms warning](https://docs.pytorch.org/vision/stable/models.html) and [DINOv2 model card](https://github.com/facebookresearch/dinov2/blob/main/MODEL_CARD.md).

The [JSON matrix](Model-Release-Matrix-2026-10-30.json) carries the full records. MD5 is used only to reconcile the trainer's inventory; use SHA256 for release integrity. No new accuracy or clean-machine acceptance result is claimed, and no model was promoted.

## Weight-by-weight record

### 1. roadscan_baseline_best.pt

SHA256: `2bb146ad53a3ddd149320aae3be67b2b1d50ccf0fdbc909edd749538055a2551`

Size: 5,536,234 bytes; role: `road_detector`.

| Question | Evidence / decision |
|---|---|
| Permission | Approved by owner; no rank/top-five privacy hold. |
| Parent | Official yolo11n.pt; parent SHA256 0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1. |
| Source available | Published baseline packet: notebook, six preparation/training Python files, two configs and two dependency files; exact eleven-file grant applied. |
| Terms | AGPL-3.0 notice and approved scoped source grant distributed with source packet; no whole-app relicense. |
| Publication | PUBLISHED: anonymous download and exact SHA verified on 28 October; release still listed on 30 October. |
| Smallest missing input | None for the existing weight/source download. Fresh public-download-to-inference acceptance remains stopped; do not present it as passed. |
| Reproducibility limits | Recorded baseline experiment exists; this audit does not rerun training or the US holdout. |
| Tests | Earlier isolated CPU inference recorded; fresh download-to-inference acceptance not completed. |

[Download original weight](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/2bb146ad53a3-roadscan_baseline_best.pt).

Evidence: [source 1](https://github.com/Feras-MQ/RoadScan/releases/tag/model-resources-2026-10-28), [source 2](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/RoadScan-Baseline-Source-AGPL-3.0.zip).

### 2. road_damage_rtdetr_x_best_Epoch001_mAP50_95_0.00000.pt

SHA256: `bda15131e5f68a3a010dcec312f343b9e54e90f4828efdb21a2f64fb342cc447`

Size: 540,036,156 bytes; role: `road_detector`.

| Question | Evidence / decision |
|---|---|
| Permission | Approved by owner; no rank/top-five privacy hold. |
| Parent | Saved initializer filename candidate(s): rtdetr-x.pt; exact parent bytes not established. |
| Source available | Saved class map/configuration and embedded Ultralytics implementation/version evidence; exact run code or patch confirmation absent. |
| Terms | Embedded AGPL-3.0 notice; preserve it. Source completeness is unverified, not proof of infringement. |
| Publication | HOLD: asset source mapping has not been established. |
| Smallest missing input | Trainer confirmation identifying the recorded stock Ultralytics version and whether it was modified; provide any actual patches/covered custom code with existing terms. Identify the initializer source (or state trained from scratch). A historical notebook is not mandatory if an equivalent complete source description is available. |
| Reproducibility limits | Exact data/split/selection lineage and independent evaluation remain unverified; these do not alone prohibit publication or private inference. |
| Tests | No new inference or accuracy test in this documentation audit. |

Evidence: [source 1](detector-config-provenance-map.json), [source 2](public-model-inventory.json).

### 3. road_damage_rtdetr_x_final_best_Epoch050_mAP50_95_0.04830.pt

SHA256: `edb35d3cf7b115d56a7bc96c6e4505c4a1da50ae1aecdf80742f49bae2a75a6d`

Size: 135,456,021 bytes; role: `road_detector`.

Trainer MD5 `e0cefd5593683edd4aac24d2fceda17d` matches the original bytes.

| Question | Evidence / decision |
|---|---|
| Permission | Approved by owner; no rank/top-five privacy hold. |
| Parent | Trainer identifies rtdetr-x.pt; exact historical parent bytes not proven. |
| Source available | Saved class map/configuration and embedded Ultralytics implementation/version evidence; exact run code or patch confirmation absent. |
| Terms | Embedded AGPL-3.0 notice; preserve it. Source completeness is unverified, not proof of infringement. |
| Publication | HOLD only this older-machine asset: checkpoint identity verified, but the supplied statement expressly retains the original-trainer/library-modification caveat. |
| Smallest missing input | Original trainer confirms the recorded stock package/version was unmodified, or supplies the actual modifications and terms. |
| Reproducibility limits | Exact data/split/selection lineage and independent evaluation remain unverified; these do not alone prohibit publication or private inference. |
| Tests | No new inference or accuracy test in this documentation audit. |

Evidence: [source 1](detector-config-provenance-map.json), [source 2](public-model-inventory.json), [source 3](Trainer-Provenance-2026-10-31.md).

### 4. road_damage_yolo11m_best_Epoch086_mAP50_95_0.21440.pt

SHA256: `9e2a0484d6f4fc7938d7e5014673f080d6bb97f697b45e8676325db76131836a`

Size: 40,526,764 bytes; role: `road_detector`.

Trainer MD5 `736286e081736b334b7a7d3a52a26da1` matches the original bytes.

| Question | Evidence / decision |
|---|---|
| Permission | Approved by owner; no rank/top-five privacy hold. |
| Parent | Trainer identifies yolo11m.pt; exact historical parent bytes not proven. |
| Source available | Saved class map/configuration and embedded Ultralytics implementation/version evidence; exact run code or patch confirmation absent. |
| Terms | Embedded AGPL-3.0 notice; preserve it. Source completeness is unverified, not proof of infringement. |
| Publication | HOLD only this older-machine asset: checkpoint identity verified, but the supplied statement expressly retains the original-trainer/library-modification caveat. |
| Smallest missing input | Original trainer confirms the recorded stock package/version was unmodified, or supplies the actual modifications and terms. |
| Reproducibility limits | Exact data/split/selection lineage and independent evaluation remain unverified; these do not alone prohibit publication or private inference. |
| Tests | No new inference or accuracy test in this documentation audit. |

Evidence: [source 1](detector-config-provenance-map.json), [source 2](public-model-inventory.json), [source 3](Trainer-Provenance-2026-10-31.md).

### 5. road_damage_yolov8m_optimized_best_Epoch097_mAP50_95_0.21809.pt

SHA256: `9a13443ad7a3f71c211059cc9b62e67e4157f7b49680d75a9ffca96742967e97`

Size: 52,041,426 bytes; role: `road_detector`.

Trainer MD5 `6651368ff9a2fadeb8723dd0aa224d64` matches the original bytes.

| Question | Evidence / decision |
|---|---|
| Permission | Approved by owner; no rank/top-five privacy hold. |
| Parent | Trainer identifies yolov8m.pt; exact historical parent bytes not proven. |
| Source available | Saved class map/configuration and embedded Ultralytics implementation/version evidence; exact run code or patch confirmation absent. |
| Terms | Embedded AGPL-3.0 notice; preserve it. Source completeness is unverified, not proof of infringement. |
| Publication | HOLD only this older-machine asset: checkpoint identity verified, but the supplied statement expressly retains the original-trainer/library-modification caveat. |
| Smallest missing input | Original trainer confirms the recorded stock package/version was unmodified, or supplies the actual modifications and terms. |
| Reproducibility limits | Exact data/split/selection lineage and independent evaluation remain unverified; these do not alone prohibit publication or private inference. |
| Tests | No new inference or accuracy test in this documentation audit. |

Evidence: [source 1](detector-config-provenance-map.json), [source 2](public-model-inventory.json), [source 3](Trainer-Provenance-2026-10-31.md).

### 6. RTDETR_L_RDD2022_200E_800px_best_Epoch068_mAP50_95_0.31278.pt

SHA256: `b636269a303539174ab208d125ab60de149fe832c4fda7aa4c25c8f109b45b60`

Size: 263,739,370 bytes; role: `road_detector`.

Trainer MD5 `fbd53dea100c7164fcf4a2293e62bafc` matches the original bytes.

| Question | Evidence / decision |
|---|---|
| Permission | Approved by owner; no rank/top-five privacy hold. |
| Parent | Trainer identifies rtdetr-l.pt; exact historical parent bytes not proven. |
| Source available | Saved class map/configuration and embedded Ultralytics implementation/version evidence; exact run code or patch confirmation absent. |
| Terms | Embedded AGPL-3.0 notice; preserve it. Source completeness is unverified, not proof of infringement. |
| Publication | HOLD only this older-machine asset: checkpoint identity verified, but the supplied statement expressly retains the original-trainer/library-modification caveat. |
| Smallest missing input | Original trainer confirms the recorded stock package/version was unmodified, or supplies the actual modifications and terms. |
| Reproducibility limits | Exact data/split/selection lineage and independent evaluation remain unverified; these do not alone prohibit publication or private inference. |
| Tests | No new inference or accuracy test in this documentation audit. |

Evidence: [source 1](detector-config-provenance-map.json), [source 2](public-model-inventory.json), [source 3](Trainer-Provenance-2026-10-31.md).

### 7. setup_benchmark_best_Epoch001_mAP50_95_0.00001.pt

SHA256: `11602fd792d5f68427d254c9613a60ca3e077bcf42ddc4dc46c6ea1fad17c698`

Size: 135,449,685 bytes; role: `road_detector`.

| Question | Evidence / decision |
|---|---|
| Permission | Approved by owner; no rank/top-five privacy hold. |
| Parent | Saved initializer filename candidate(s): rtdetr-x.pt; exact parent bytes not established. |
| Source available | Saved class map/configuration and embedded Ultralytics implementation/version evidence; exact run code or patch confirmation absent. |
| Terms | Embedded AGPL-3.0 notice; preserve it. Source completeness is unverified, not proof of infringement. |
| Publication | HOLD: asset source mapping has not been established. |
| Smallest missing input | Trainer confirmation identifying the recorded stock Ultralytics version and whether it was modified; provide any actual patches/covered custom code with existing terms. Identify the initializer source (or state trained from scratch). A historical notebook is not mandatory if an equivalent complete source description is available. |
| Reproducibility limits | Exact data/split/selection lineage and independent evaluation remain unverified; these do not alone prohibit publication or private inference. |
| Tests | No new inference or accuracy test in this documentation audit. |

Evidence: [source 1](detector-config-provenance-map.json), [source 2](public-model-inventory.json).

### 8. YOLO11s_RDD2022_200E_800px_best_Epoch085_mAP50_95_0.34684.pt

SHA256: `e1937609619f0172b0765d676cd0b8167adbda979cb4d3cabeaf61e6395b7758`

Size: 19,219,610 bytes; role: `road_detector`.

Trainer MD5 `63334fe8b3734035a9d5335478ad0411` matches the original bytes.

| Question | Evidence / decision |
|---|---|
| Permission | Approved by owner; no rank/top-five privacy hold. |
| Parent | Trainer identifies yolo11s.pt; exact historical parent bytes not proven. |
| Source available | Saved class map/configuration and embedded Ultralytics implementation/version evidence; exact run code or patch confirmation absent. |
| Terms | Embedded AGPL-3.0 notice; preserve it. Source completeness is unverified, not proof of infringement. |
| Publication | HOLD only this older-machine asset: checkpoint identity verified, but the supplied statement expressly retains the original-trainer/library-modification caveat. |
| Smallest missing input | Original trainer confirms the recorded stock package/version was unmodified, or supplies the actual modifications and terms. |
| Reproducibility limits | Exact data/split/selection lineage and independent evaluation remain unverified; these do not alone prohibit publication or private inference. |
| Tests | No new inference or accuracy test in this documentation audit. |

Evidence: [source 1](detector-config-provenance-map.json), [source 2](public-model-inventory.json), [source 3](Trainer-Provenance-2026-10-31.md).

### 9. YOLOv8m_RDD2022_150E_800px_best_Epoch021_mAP50_95_0.30855.pt

SHA256: `4e14d23d45da6d74504f24632d3f58b447ed6310caf1129b141c736f77e556c1`

Size: 103,884,827 bytes; role: `road_detector`.

Trainer MD5 `30600686e5a814e92942ef419720b1fc` matches the original bytes.

| Question | Evidence / decision |
|---|---|
| Permission | Approved by owner; no rank/top-five privacy hold. |
| Parent | Trainer identifies own resumed last.pt; original initializer unconfirmed (yolov8m.pt is only a suggestion); exact historical parent bytes not proven. |
| Source available | Saved class map/configuration and embedded Ultralytics implementation/version evidence; exact run code or patch confirmation absent. |
| Terms | Embedded AGPL-3.0 notice; preserve it. Source completeness is unverified, not proof of infringement. |
| Publication | HOLD only this older-machine asset: checkpoint identity verified, but the supplied statement expressly retains the original-trainer/library-modification caveat. |
| Smallest missing input | Original trainer confirms the recorded stock package/version was unmodified, or supplies the actual modifications and terms. Also identify the original initializer of the resumed run; do not promote the suggested yolov8m.pt to a fact. |
| Reproducibility limits | Exact data/split/selection lineage and independent evaluation remain unverified; these do not alone prohibit publication or private inference. |
| Tests | No new inference or accuracy test in this documentation audit. |

Evidence: [source 1](detector-config-provenance-map.json), [source 2](public-model-inventory.json), [source 3](Trainer-Provenance-2026-10-31.md).

### 10. yolo11n.pt

SHA256: `0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1`

Size: 5,613,764 bytes; role: `stock_coco`.

| Question | Evidence / decision |
|---|---|
| Permission | Approved by owner; no rank/top-five privacy hold. |
| Parent | Official Ultralytics COCO-pretrained YOLO11n initializer; not team-trained. |
| Source available | Official Ultralytics implementation and upstream asset; source/notices remain upstream. |
| Terms | Upstream Ultralytics terms; no new license is assigned. |
| Publication | UPSTREAM DOWNLOAD: exact file/hash previously verified; no RoadScan mirror. |
| Smallest missing input | None for the official link. This is not a road-damage model. |
| Reproducibility limits | Does not reproduce RoadScan training and cannot replace a trained road detector. |
| Tests | No new inference or accuracy test in this documentation audit. |

[Download original weight](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt).

Evidence: [source 1](https://github.com/ultralytics/ultralytics), [source 2](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt).

### 11. e2_yolo26s_640.pt

SHA256: `31b518ed36ec022fcadb0768268d4b6686a4c327bec3a9cd4fe5fc722ee4cc83`

Size: 20,318,592 bytes; role: `road_detector`.

Trainer MD5 `4fd8bb20b1424da7694c7a88f39150bf` matches the original bytes.

| Question | Evidence / decision |
|---|---|
| Permission | Approved by owner; no rank/top-five privacy hold. |
| Parent | Trainer identifies stock COCO yolo26s.pt; exact historical initializer hash not independently established. |
| Source available | Verified official pip source archive for Ultralytics 8.4.177; trainer confirms stock library without modifications. Trainer identifies ordinary CLI training arguments; original RunPod orchestration wrapper is absent, not invented. |
| Terms | Existing embedded AGPL-3.0 notice retained. Source mapping updated using trainer attestation plus verified official source; no new or whole-app license assigned. |
| Publication | PUBLISHED 31 October: original bytes anonymously downloaded and exact SHA256/size verified; adjacent source/notices included. |
| Smallest missing input | None for this published asset/source packet. Historical parent hashes, full training data/evaluator and selection details remain reproduction limits, not automatic publication prohibitions. |
| Reproducibility limits | Exact data/split/selection lineage and independent evaluation remain unverified; these do not alone prohibit publication or private inference. |
| Tests | No new inference or accuracy test in this documentation audit. |

[Download original weight](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/31b518ed36ec-e2_yolo26s_640.pt).

Evidence: [source 1](detector-config-provenance-map.json), [source 2](public-model-inventory.json), [source 3](Trainer-Provenance-2026-10-31.md), [source 4](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/RoadScan-Team-Model-Source-2026-10-31.zip), [source 5](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/RoadScan-Team-Models-2026-10-31.json), [source 6](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/RoadScan-Team-Models-2026-10-31-SHA256SUMS.txt).

### 12. data_yolo26s_640_clean_labels.pt

SHA256: `1bb6724ee2d01cf0f64c81ae8b6845c70ba06776d51b189f0f3052f880e96543`

Size: 20,318,592 bytes; role: `road_detector`.

Trainer MD5 `0e0296b8c153a49aab9413ffc6032218` matches the original bytes.

| Question | Evidence / decision |
|---|---|
| Permission | Approved by owner; no rank/top-five privacy hold. |
| Parent | Trainer identifies stock COCO yolo26s.pt; exact historical initializer hash not independently established. |
| Source available | Verified official pip source archive for Ultralytics 8.4.177; trainer confirms stock library without modifications. Trainer identifies ordinary CLI training arguments; original RunPod orchestration wrapper is absent, not invented. |
| Terms | Existing embedded AGPL-3.0 notice retained. Source mapping updated using trainer attestation plus verified official source; no new or whole-app license assigned. |
| Publication | PUBLISHED 31 October: original bytes anonymously downloaded and exact SHA256/size verified; adjacent source/notices included. |
| Smallest missing input | None for this published asset/source packet. Historical parent hashes, full training data/evaluator and selection details remain reproduction limits, not automatic publication prohibitions. |
| Reproducibility limits | Exact data/split/selection lineage and independent evaluation remain unverified; these do not alone prohibit publication or private inference. |
| Tests | No new inference or accuracy test in this documentation audit. |

[Download original weight](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/1bb6724ee2d0-data_yolo26s_640_clean_labels.pt).

Evidence: [source 1](detector-config-provenance-map.json), [source 2](public-model-inventory.json), [source 3](Trainer-Provenance-2026-10-31.md), [source 4](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/RoadScan-Team-Model-Source-2026-10-31.zip), [source 5](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/RoadScan-Team-Models-2026-10-31.json), [source 6](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/RoadScan-Team-Models-2026-10-31-SHA256SUMS.txt).

### 13. main_yolo26s_1024.pt

SHA256: `9f940caa92229f503eef1171010c13ee8fd74d7b69300e959357d6a8d14be434`

Size: 20,414,080 bytes; role: `road_detector`.

Trainer MD5 `702e8a0b44b1e8bb0eceda92cce3b3c2` matches the original bytes.

| Question | Evidence / decision |
|---|---|
| Permission | Approved by owner; no rank/top-five privacy hold. |
| Parent | Trainer identifies stock COCO yolo26s.pt; exact historical initializer hash not independently established. |
| Source available | Verified official pip source archive for Ultralytics 8.4.177; trainer confirms stock library without modifications. Trainer identifies ordinary CLI training arguments; original RunPod orchestration wrapper is absent, not invented. |
| Terms | Existing embedded AGPL-3.0 notice retained. Source mapping updated using trainer attestation plus verified official source; no new or whole-app license assigned. |
| Publication | PUBLISHED 31 October: original bytes anonymously downloaded and exact SHA256/size verified; adjacent source/notices included. |
| Smallest missing input | None for this published asset/source packet. Historical parent hashes, full training data/evaluator and selection details remain reproduction limits, not automatic publication prohibitions. |
| Reproducibility limits | Exact data/split/selection lineage and independent evaluation remain unverified; these do not alone prohibit publication or private inference. Saved epoch is -1; original main mixed-data manifest remains absent. |
| Tests | 29 October: restricted loader plus actual CPU inference at 1024 on one synthetic and one road image completed. 30 October: selected main model verified unchanged. Compatibility only; no accuracy measurement. |

[Download original weight](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/9f940caa9222-main_yolo26s_1024.pt).

Evidence: [source 1](detector-config-provenance-map.json), [source 2](public-model-inventory.json), [source 3](Trainer-Provenance-2026-10-31.md), [source 4](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/RoadScan-Team-Model-Source-2026-10-31.zip), [source 5](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/RoadScan-Team-Models-2026-10-31.json), [source 6](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/RoadScan-Team-Models-2026-10-31-SHA256SUMS.txt).

### 14. e2_yolo26n_640.pt

SHA256: `3be62681e3ecc306fd4fbbbcbd40f805fcdd092d03cd57373695ca0453b1aaf8`

Size: 5,463,296 bytes; role: `road_detector`.

Trainer MD5 `1d8aca51755f4b390ce54f106fbcf22f` matches the original bytes.

| Question | Evidence / decision |
|---|---|
| Permission | Approved by owner; no rank/top-five privacy hold. |
| Parent | Trainer identifies stock COCO yolo26n.pt; exact historical initializer hash not independently established. |
| Source available | Verified official pip source archive for Ultralytics 8.4.177; trainer confirms stock library without modifications. Trainer identifies ordinary CLI training arguments; original RunPod orchestration wrapper is absent, not invented. |
| Terms | Existing embedded AGPL-3.0 notice retained. Source mapping updated using trainer attestation plus verified official source; no new or whole-app license assigned. |
| Publication | PUBLISHED 31 October: original bytes anonymously downloaded and exact SHA256/size verified; adjacent source/notices included. |
| Smallest missing input | None for this published asset/source packet. Historical parent hashes, full training data/evaluator and selection details remain reproduction limits, not automatic publication prohibitions. |
| Reproducibility limits | Exact data/split/selection lineage and independent evaluation remain unverified; these do not alone prohibit publication or private inference. |
| Tests | No new inference or accuracy test in this documentation audit. |

[Download original weight](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/3be62681e3ec-e2_yolo26n_640.pt).

Evidence: [source 1](detector-config-provenance-map.json), [source 2](public-model-inventory.json), [source 3](Trainer-Provenance-2026-10-31.md), [source 4](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/RoadScan-Team-Model-Source-2026-10-31.zip), [source 5](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/RoadScan-Team-Models-2026-10-31.json), [source 6](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/RoadScan-Team-Models-2026-10-31-SHA256SUMS.txt).

### 15. e3_yolo26s_640_no_augmentation.pt

SHA256: `3ef405bf22a9324c1f8d43537e21e454a9b4df82cd08f7cb9a09d7d80d1f6edf`

Size: 20,318,592 bytes; role: `road_detector`.

Trainer MD5 `19a0ee638e668683c1544cc1e4086865` matches the original bytes.

| Question | Evidence / decision |
|---|---|
| Permission | Approved by owner; no rank/top-five privacy hold. |
| Parent | Trainer identifies stock COCO yolo26s.pt; exact historical initializer hash not independently established. |
| Source available | Verified official pip source archive for Ultralytics 8.4.177; trainer confirms stock library without modifications. Trainer identifies ordinary CLI training arguments; original RunPod orchestration wrapper is absent, not invented. |
| Terms | Existing embedded AGPL-3.0 notice retained. Source mapping updated using trainer attestation plus verified official source; no new or whole-app license assigned. |
| Publication | PUBLISHED 31 October: original bytes anonymously downloaded and exact SHA256/size verified; adjacent source/notices included. |
| Smallest missing input | None for this published asset/source packet. Historical parent hashes, full training data/evaluator and selection details remain reproduction limits, not automatic publication prohibitions. |
| Reproducibility limits | Exact data/split/selection lineage and independent evaluation remain unverified; these do not alone prohibit publication or private inference. |
| Tests | No new inference or accuracy test in this documentation audit. |

[Download original weight](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/3ef405bf22a9-e3_yolo26s_640_no_augmentation.pt).

Evidence: [source 1](detector-config-provenance-map.json), [source 2](public-model-inventory.json), [source 3](Trainer-Provenance-2026-10-31.md), [source 4](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/RoadScan-Team-Model-Source-2026-10-31.zip), [source 5](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/RoadScan-Team-Models-2026-10-31.json), [source 6](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/RoadScan-Team-Models-2026-10-31-SHA256SUMS.txt).

### 16. e3_yolo26s_640_vertical_flip.pt

SHA256: `63d2099e766f5a6ee8bcc7bd915487b99ec03a7da33940c279e844954bf91e08`

Size: 20,318,720 bytes; role: `road_detector`.

Trainer MD5 `711ef23a36f6393a4092bafa80dcb3c2` matches the original bytes.

| Question | Evidence / decision |
|---|---|
| Permission | Approved by owner; no rank/top-five privacy hold. |
| Parent | Trainer identifies stock COCO yolo26s.pt; exact historical initializer hash not independently established. Originally yolo26s.pt; resumed this run from weights/last.pt after a crash. |
| Source available | Verified official pip source archive for Ultralytics 8.4.177; trainer confirms stock library without modifications. Trainer identifies ordinary CLI training arguments; original RunPod orchestration wrapper is absent, not invented. |
| Terms | Existing embedded AGPL-3.0 notice retained. Source mapping updated using trainer attestation plus verified official source; no new or whole-app license assigned. |
| Publication | PUBLISHED 31 October: original bytes anonymously downloaded and exact SHA256/size verified; adjacent source/notices included. |
| Smallest missing input | None for this published asset/source packet. Historical parent hashes, full training data/evaluator and selection details remain reproduction limits, not automatic publication prohibitions. |
| Reproducibility limits | Exact data/split/selection lineage and independent evaluation remain unverified; these do not alone prohibit publication or private inference. |
| Tests | No new inference or accuracy test in this documentation audit. |

[Download original weight](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/63d2099e766f-e3_yolo26s_640_vertical_flip.pt).

Evidence: [source 1](detector-config-provenance-map.json), [source 2](public-model-inventory.json), [source 3](Trainer-Provenance-2026-10-31.md), [source 4](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/RoadScan-Team-Model-Source-2026-10-31.zip), [source 5](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/RoadScan-Team-Models-2026-10-31.json), [source 6](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/RoadScan-Team-Models-2026-10-31-SHA256SUMS.txt).

### 17. e4_yolo26s_640_without_India.pt

SHA256: `fa148e7109aad2f30075305bc46e53c8c24fbc6c29ed7167436a30de2acb16bb`

Size: 20,318,592 bytes; role: `road_detector`.

Trainer MD5 `5109fbaf4f3f9bec3853a7c0091f2bc8` matches the original bytes.

| Question | Evidence / decision |
|---|---|
| Permission | Approved by owner; no rank/top-five privacy hold. |
| Parent | Trainer identifies stock COCO yolo26s.pt; exact historical initializer hash not independently established. |
| Source available | Verified official pip source archive for Ultralytics 8.4.177; trainer confirms stock library without modifications. Trainer identifies ordinary CLI training arguments; original RunPod orchestration wrapper is absent, not invented. |
| Terms | Existing embedded AGPL-3.0 notice retained. Source mapping updated using trainer attestation plus verified official source; no new or whole-app license assigned. |
| Publication | PUBLISHED 31 October: original bytes anonymously downloaded and exact SHA256/size verified; adjacent source/notices included. |
| Smallest missing input | None for this published asset/source packet. Historical parent hashes, full training data/evaluator and selection details remain reproduction limits, not automatic publication prohibitions. |
| Reproducibility limits | Exact data/split/selection lineage and independent evaluation remain unverified; these do not alone prohibit publication or private inference. |
| Tests | No new inference or accuracy test in this documentation audit. |

[Download original weight](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/fa148e7109aa-e4_yolo26s_640_without_India.pt).

Evidence: [source 1](detector-config-provenance-map.json), [source 2](public-model-inventory.json), [source 3](Trainer-Provenance-2026-10-31.md), [source 4](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/RoadScan-Team-Model-Source-2026-10-31.zip), [source 5](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/RoadScan-Team-Models-2026-10-31.json), [source 6](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/RoadScan-Team-Models-2026-10-31-SHA256SUMS.txt).

### 18. baseline_resnet18.pt

SHA256: `267c1eefc78dedf7fe13e9d2e899695b7f5d1edefa98ee7115356d2c6d47b21c`

Size: 44,793,483 bytes; role: `classifier`.

Trainer MD5 `447c958de19105ea2ce5d0bedc691763` matches the original bytes.

| Question | Evidence / decision |
|---|---|
| Permission | Approved by owner; no rank/top-five privacy hold. |
| Parent | Trainer identifies torchvision ResNet18_Weights.IMAGENET1K_V1 (not scratch), four output labels, 20 epochs at 512px on RDD train. MD5 and current SHA256 match; historical initializer bytes not hashed. |
| Source available | Official torchvision ResNet18 source/weight enum identified; trainer points to training/baseline_classifier.py build_model line 118, but that original file was not included in the reviewed archives. |
| Terms | Torchvision repository is BSD-3-Clause; official model documentation warns pretrained weights may carry separate terms. An explicit redistribution basis for this pretrained-weight derivative has not been established; no illegal-use conclusion is inferred. |
| Publication | HOLD only ResNet18: initializer identity clarified; pretrained-weight redistribution terms remain unresolved. |
| Smallest missing input | Asset-specific terms or authoritative redistribution confirmation for the identified IMAGENET1K_V1 initializer/derivative; original training script is a separate reproduction input, not by itself a BSD restriction. |
| Reproducibility limits | Original training recipe and split lineage are missing; replacement synthetic tests are not reproduction of this weight. |
| Tests | No new inference or accuracy test in this documentation audit. |

Evidence: [source 1](Team-Models-and-Results.md), [source 2](https://docs.pytorch.org/vision/stable/models.html), [source 3](Trainer-Provenance-2026-10-31.md), [source 4](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.resnet18.html), [source 5](https://github.com/pytorch/vision/blob/main/LICENSE).

### 19. dinov2_vits14_pretrain.pth

SHA256: `b938bf1bc15cd2ec0feacfe3a1bb553fe8ea9ca46a7e1d8d00217f29aef60cd9`

Size: 88,283,115 bytes; role: `embedding`.

| Question | Evidence / decision |
|---|---|
| Permission | Approved by owner; no rank/top-five privacy hold. |
| Parent | Unmodified official Meta DINOv2 ViT-S/14 pretrained backbone. |
| Source available | Official DINOv2 source/model card; published Apache license and provenance packet. |
| Terms | Apache-2.0 model/source evidence; notices shipped with the mirror. |
| Publication | PUBLISHED: anonymous download and exact SHA verified on 28 October; release still listed on 30 October. |
| Smallest missing input | None for redistribution of the unchanged published asset. Real duplicate-pair calibration is a separate task. |
| Reproducibility limits | Does not detect boxes. Real-pair retrieval and threshold validation remain unmeasured. |
| Tests | No new inference or accuracy test in this documentation audit. |

[Download original weight](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/b938bf1bc15c-dinov2_vits14_pretrain.pth).

Evidence: [source 1](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/DINOv2-license-provenance.zip), [source 2](https://github.com/facebookresearch/dinov2/blob/main/MODEL_CARD.md).

### 20. 2_road_v1_yolo26s_1024_RECOMMENDED.pt

SHA256: `78f5e2afb82d5145f30de9957cb51f167241e377ed0b5775f71be1c5e80ac87d`

Size: 20,444,878 bytes; role: `road_detector`.

Trainer MD5 `136263d2f425bd02e6aa99ce3302fa7b` matches the original bytes.

| Question | Evidence / decision |
|---|---|
| Permission | Owner authorized inclusion/publication of eligible new team models; no extra rank/selection approval required. |
| Parent | Trainer-attested parent SHA identity 9f940caa92229f503eef1171010c13ee8fd74d7b69300e959357d6a8d14be434; package filename/metadata support this lineage, but do not prove historical parent bytes. |
| Source available | Verified official pip source archive for Ultralytics 8.4.175; trainer confirms stock library without modifications. Previously approved nine-file fine-tune source is also included. |
| Terms | Existing embedded AGPL-3.0 notice retained. Source mapping updated using trainer attestation plus verified official source; no new or whole-app license assigned. |
| Publication | PUBLISHED 31 October: original bytes anonymously downloaded and exact SHA256/size verified; adjacent source/notices included. |
| Smallest missing input | None for this published asset/source packet. Historical parent hashes, full training data/evaluator and selection details remain reproduction limits, not automatic publication prohibitions. |
| Reproducibility limits | Supplied v1 selection rule rejects all recorded epochs; actual manual selection/export explanation missing. Road set was used in selection, shares video sequences across partitions, and big-test evaluator is absent; supplied scores are not independent held-out accuracy. Trainer reports only a list-output-directory change in the earlier A/B helper; no recipe/data change. Historical v1 selection explanation remains unresolved. |
| Tests | 29 October: restricted loading and actual CPU1024 inference on one synthetic and one road image passed. 30 October: distinct experimental choice visible in model library; not activated. No accuracy or sustained-speed claim. |

[Download original weight](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/78f5e2afb82d-main_yolo26s_1024_road.pt).

Evidence: [source 1](../model_sources/road-finetunes-2026-10-29/NOTICE.md), [source 2](../model_sources/road-finetunes-2026-10-29/Source-Manifest.json), [source 3](../model_sources/road-finetunes-2026-10-29/Model-Metadata.json), [source 4](../model_sources/road-finetunes-2026-10-29/README.md), [source 5](Trainer-Provenance-2026-10-31.md), [source 6](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/RoadScan-Team-Model-Source-2026-10-31.zip), [source 7](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/RoadScan-Team-Models-2026-10-31.json), [source 8](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/RoadScan-Team-Models-2026-10-31-SHA256SUMS.txt).

### 21. 3_road_A_yolo26s_1024.pt

SHA256: `00794102e39e621f1268e31f43b3743daae17309b5eaf90feef1077f0bf0991b`

Size: 20,446,971 bytes; role: `road_detector`.

Trainer MD5 `3f5da7ce51d4440f88678917149afa9b` matches the original bytes.

| Question | Evidence / decision |
|---|---|
| Permission | Owner authorized inclusion/publication of eligible new team models; no extra rank/selection approval required. |
| Parent | Trainer-attested parent SHA identity 9f940caa92229f503eef1171010c13ee8fd74d7b69300e959357d6a8d14be434; package filename/metadata support this lineage, but do not prove historical parent bytes. |
| Source available | Verified official pip source archive for Ultralytics 8.4.175; trainer confirms stock library without modifications. Previously approved nine-file fine-tune source is also included. |
| Terms | Existing embedded AGPL-3.0 notice retained. Source mapping updated using trainer attestation plus verified official source; no new or whole-app license assigned. |
| Publication | PUBLISHED 31 October: original bytes anonymously downloaded and exact SHA256/size verified; adjacent source/notices included. |
| Smallest missing input | None for this published asset/source packet. Historical parent hashes, full training data/evaluator and selection details remain reproduction limits, not automatic publication prohibitions. |
| Reproducibility limits | Saved selection rule is consistent with epoch 4; exact historical parent hash unverified. Road set was used in selection, shares video sequences across partitions, and big-test evaluator is absent; supplied scores are not independent held-out accuracy. Trainer reports only a list-output-directory change in the earlier A/B helper; no recipe/data change. Historical v1 selection explanation remains unresolved. |
| Tests | 29 October: restricted loading and actual CPU1024 inference on one synthetic and one road image passed. 30 October: distinct experimental choice visible in model library; not activated. No accuracy or sustained-speed claim. |

[Download original weight](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/00794102e39e-main_yolo26s_1024_road_v2.pt).

Evidence: [source 1](../model_sources/road-finetunes-2026-10-29/NOTICE.md), [source 2](../model_sources/road-finetunes-2026-10-29/Source-Manifest.json), [source 3](../model_sources/road-finetunes-2026-10-29/Model-Metadata.json), [source 4](../model_sources/road-finetunes-2026-10-29/README.md), [source 5](Trainer-Provenance-2026-10-31.md), [source 6](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/RoadScan-Team-Model-Source-2026-10-31.zip), [source 7](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/RoadScan-Team-Models-2026-10-31.json), [source 8](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/RoadScan-Team-Models-2026-10-31-SHA256SUMS.txt).

### 22. 4_road_v2b_yolo26s_1024.pt

SHA256: `0caef4521c82a944cfe4b6e5022914eeabab9c69864967db17a9915f4fdc7500`

Size: 20,447,626 bytes; role: `road_detector`.

Trainer MD5 `2062c17bf58470639354ada10fefe6da` matches the original bytes.

| Question | Evidence / decision |
|---|---|
| Permission | Owner authorized inclusion/publication of eligible new team models; no extra rank/selection approval required. |
| Parent | Trainer-attested parent SHA identity 78f5e2afb82d5145f30de9957cb51f167241e377ed0b5775f71be1c5e80ac87d; package filename/metadata support this lineage, but do not prove historical parent bytes. |
| Source available | Verified official pip source archive for Ultralytics 8.4.175; trainer confirms stock library without modifications. Previously approved nine-file fine-tune source is also included. |
| Terms | Existing embedded AGPL-3.0 notice retained. Source mapping updated using trainer attestation plus verified official source; no new or whole-app license assigned. |
| Publication | PUBLISHED 31 October: original bytes anonymously downloaded and exact SHA256/size verified; adjacent source/notices included. |
| Smallest missing input | None for this published asset/source packet. Historical parent hashes, full training data/evaluator and selection details remain reproduction limits, not automatic publication prohibitions. |
| Reproducibility limits | Saved selection rule is consistent with epoch 3; exact historical parent hash unverified. Road set was used in selection, shares video sequences across partitions, and big-test evaluator is absent; supplied scores are not independent held-out accuracy. Trainer reports only a list-output-directory change in the earlier A/B helper; no recipe/data change. Historical v1 selection explanation remains unresolved. |
| Tests | 29 October: restricted loading and actual CPU1024 inference on one synthetic and one road image passed. 30 October: distinct experimental choice visible in model library; not activated. No accuracy or sustained-speed claim. |

[Download original weight](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/0caef4521c82-main_yolo26s_1024_road_v2b.pt).

Evidence: [source 1](../model_sources/road-finetunes-2026-10-29/NOTICE.md), [source 2](../model_sources/road-finetunes-2026-10-29/Source-Manifest.json), [source 3](../model_sources/road-finetunes-2026-10-29/Model-Metadata.json), [source 4](../model_sources/road-finetunes-2026-10-29/README.md), [source 5](Trainer-Provenance-2026-10-31.md), [source 6](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/RoadScan-Team-Model-Source-2026-10-31.zip), [source 7](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/RoadScan-Team-Models-2026-10-31.json), [source 8](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/RoadScan-Team-Models-2026-10-31-SHA256SUMS.txt).
