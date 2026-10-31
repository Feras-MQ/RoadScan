# Trainer evidence and release update — 31 October 2026

**Ten more road detectors are published:** seven RunPod YOLO26 checkpoints and Road v1, Road A and Road v2b. Their original bytes are unchanged. Each was downloaded anonymously and matched its byte count and full SHA256, as were the three companion files.

- [Weights and source release](https://github.com/Feras-MQ/RoadScan/releases/tag/model-resources-2026-10-28)
- [Official stock source and approved fine-tune source/notices](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/RoadScan-Team-Model-Source-2026-10-31.zip)
- [Per-model provenance](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/RoadScan-Team-Models-2026-10-31.json) and [batch SHA256 checksums](https://github.com/Feras-MQ/RoadScan/releases/download/model-resources-2026-10-28/RoadScan-Team-Models-2026-10-31-SHA256SUMS.txt)
- [Current 22-model matrix](Model-Release-Matrix-2026-10-30.md) and [trainer MD5 / independent SHA256 reconciliation](Trainer-Byte-Reconciliation-2026-10-31.json)

## What is verified, and what is attested

**Verified from original bytes:** all 17 located checkpoints in the trainer's list match the supplied MD5 and existing SHA256 inventory. These include the ten newly released models, six older detectors and ResNet18. Hashing streamed the files without loading models. MD5 only reconciles the trainer's list; release integrity uses SHA256.

**Trainer attestation:** the seven RunPod models used stock pip Ultralytics 8.4.177 and ordinary training arguments; the three fine-tunes used stock pip 8.4.175. The trainer says the library was not modified. Embedded versions agree. The historical installation on another machine cannot independently be proven from a checkpoint.

Official PyPI source distributions were downloaded and hash-verified, not installed or executed:

| Version | Source archive SHA256 |
|---|---|
| 8.4.175 | `3af729abd18170778ca4cef7c9bff96874fca8e1220995d9512d81ed010bbc84` |
| 8.4.177 | `cee81b288d28dcefa725037bb8fd41674ffd1a5438162272012ac16758de93dc` |

The release packet includes both complete stock source archives and their license texts, plus the already-approved nine-file fine-tune source package. Existing checkpoint AGPL notices and the scoped team grant are retained; no new blanket license for the app or datasets is created. Source mapping is based on the trainer's stock-code confirmation, not an invented reconstruction of missing RunPod wrappers. This is distinct from exact training reproduction.

## Parent chain and reproducibility limits

The trainer identifies **Main → v1**, **Main → A**, and **v1 → v2b**. Current files have exact verified identities; saved parent filenames and the attestation support this chain but do not prove that historical parent bytes were identical. The vertical-flip RunPod experiment began from yolo26s.pt and resumed its own last.pt after a crash, according to the trainer.

The fine-tune recipe is trainer-reported: freeze 10, SGD, lr0 0.0005, lrf 0.1, zero warmup, five epochs, close_mosaic 2, size 1024, and RDD training images plus labeled road frames. The reported frame counts are 390 for v1 and 923 for A/v2b. The trainer describes an earlier A/B helper change that moved list output out of the runs directory; the recipe and data were reportedly unchanged. These counts do not establish an independent local test set.

The supplied historical v1 selector still rejects all recorded epochs under its written rule; the actual manual selection/export explanation has not been supplied. The separate big-test evaluator and complete historical split/initializer hashes remain absent. Those limits constrain reproduction and performance claims; they did not automatically prohibit release of the confirmed stock-source assets. No notebook was silently rewritten, no evaluation rerun, and no new accuracy claim made.

## Remaining assets are assessed individually

| Assets | New evidence | Remaining issue |
|---|---|---|
| Six located older detectors | Trainer MD5 matches the existing SHA256; recorded versions and initializer statements are retained | The supplied evidence expressly says the original trainer should confirm whether libraries were modified on those older machines; this caveat is not removed by the general stock-pip statement |
| YOLOv8m RDD2022 Epoch21, within that older group | Resumed an own last.pt checkpoint | The original initializer is still unconfirmed; suggested yolov8m.pt is not promoted to a fact |
| RT-DETR X Epoch1 and setup benchmark | Existing hashes and embedded metadata are retained | No specific MD5/per-run statement in the new list resolves their earlier source conditions |
| ResNet18 | MD5/SHA256 match; trainer identifies torchvision `ResNet18_Weights.IMAGENET1K_V1`, four outputs, 20 epochs at 512px | Initializer identity is now known. Applicable pretrained-weight redistribution terms remain unresolved; the original `training/baseline_classifier.py` was referenced but not supplied |
| RT-DETR-L last.pt Epoch70 (`5baf8107f5cfadfe1c76fd309149b859` MD5) | Trainer names a same-run checkpoint | Not found in the supplied model archives; no SHA256 or upload claimed |
| yolo8m_183epochs.pt (`534319ca3a63bbd46a69bf9a7be25e76` MD5) | Trainer reports a resumed YOLOv8 model | Not found in the supplied archives; its parent identity is attested only, no additional local-model count or upload claimed |

The two unlocated entries are not replacements for the verified existing files. Of the 22 verified local weight identities, twelve are now mirrored (eleven detectors and DINOv2), one stock initializer has an official link, and nine remain held individually. One uncertain initializer does not block unrelated verified releases.

[Torchvision identifies the ResNet18 weight enum](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.resnet18.html); its [code license is BSD-3-Clause](https://github.com/pytorch/vision/blob/main/LICENSE), while its [model documentation explicitly distinguishes possible pretrained-weight terms](https://docs.pytorch.org/vision/stable/models.html). This audit has not established an explicit redistribution basis for that derivative and does not infer a prohibition merely from a missing notebook or from ImageNet's name.

## Use the released models

Download the chosen `.pt` and adjacent source/notices; compare its SHA256 with the batch manifest. In RoadScan, use **Settings → Your model library → Browse models → Use model** and confirm **Active**. Import alone does not select a model. If a known hash is already installed, reuse that entry. The live workstation's selected Main model, reports and settings were not changed for this publication.

The checkpoint files retain generic training paths, including the disclosed project drive path in v1; static string/opcode inspection found no credential patterns. Raw road data, labels, reports and secrets were excluded from source/provenance artifacts. No models were deserialized or executed during this release review.

The earlier denied fresh-setup and resource-diagnostic operations remain stopped; this publication is not a passed fresh-install test. The report/slides remain dated snapshots supplemented by this note; UI overhaul and Hermes have not resumed.
