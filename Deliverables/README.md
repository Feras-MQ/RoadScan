# RoadScan instructor deliverables

**31 October update:** [ten additional model downloads and trainer provenance](Trainer-Provenance-2026-10-31.md); the [22-model matrix](Model-Release-Matrix-2026-10-30.md) now separates twelve mirrored weights, one upstream initializer and nine individual holds. The presentation and speaker notes now reflect the 31 October model release; the report remains a dated snapshot.

**Team:** Feras Alyamani, Ahmed Salamah, Ahmed Alhejaili. **Release:** 2026-10-27.1. **Prepared:** 27 October 2026.

Start with the report PDF and the [30 October supplement](Submission-Audit-2026-10-30.md), then the presentation. Source code is in the repository root; the report retains its dated 27 October snapshot, and the presentation was refreshed on 31 October. The [current 22-weight matrix](Model-Release-Matrix-2026-10-30.md) separates publication permission, source terms and missing evaluations for every model; the older 19-weight inventory and model report are historical snapshots.

| File | Contents | Status |
|---|---|---|
| [RoadScan-Project-Report.pdf](RoadScan-Project-Report.pdf) | Full report, results, screenshots and appendices; 18 pages | PDF visually checked |
| [RoadScan-Project-Report.docx](RoadScan-Project-Report.docx) | Editable report | Content checked; Word pagination unverified |
| [RoadScan-Presentation.pdf](RoadScan-Presentation.pdf) | Static presentation; 12 slides | All slide visuals checked |
| [RoadScan-Presentation.pptx](RoadScan-Presentation.pptx) | Editable slides, diagrams and tables | Static; native PowerPoint playback unverified |
| [Speaker-Notes.txt](Speaker-Notes.txt) | English presentation script | Seven main slides, about five minutes |
| [Presentation-Guide.md](Presentation-Guide.md) | Timing and optional appendix/demo guidance | Current |
| [Quick-Start.md](Quick-Start.md) | Short source-download walkthrough | Uses the verified root setup instructions |
| [Iriun-Webcam-Guide.md](Iriun-Webcam-Guide.md) | Phone as a computer camera, permissions and automatic recognition | Official setup sources checked; physical integration unverified |
| [Run-On-Another-Computer.md](Run-On-Another-Computer.md) | Docker setup and portable-bundle guidance | Linux x86-64 CPU checked; Mac/ARM unverified |
| [Inference-and-Reproducibility.md](Inference-and-Reproducibility.md) | New-image inference without retraining; model/state checks and pinned setup | Existing API equivalent; public-download acceptance pending |
| [For-Examiners.md](For-Examiners.md) | Demonstration and evidence guide | Current public edition |
| [Collect-Photos.md](Collect-Photos.md) | Local test-photo collection and labeling | Genuine Saudi test collection remains pending |
| [Models.md](Models.md) | Historical model availability, tasks and license conditions | 28 October pre-baseline-publication snapshot; current availability is in the 30 October matrix |
| [public-model-inventory.csv](public-model-inventory.csv) / [.json](public-model-inventory.json) | Architecture/task, provenance, exact size and SHA-256 | No model weights included in these files |
| [Model-Report.pdf](Model-Report.pdf) / [.md](Model-Report.md) | All 19 models, training counts, supplied metrics and comparison limits | Historical evidence separated from pending common-set benchmark |
| [detector-config-provenance-map.json](detector-config-provenance-map.json) | Class maps and available configuration tied to 16 detector hashes | Unknown original values remain explicitly unknown |
| [Team-Models-and-Results.md](Team-Models-and-Results.md) | Supplied training evidence and model results | Historical results; not a new fair ranking |
| [Validation-Status.md](Validation-Status.md) | Verified checks and remaining limitations | Full common-set benchmark pending |

Technical documentation: [camera and models](../docs/LIVE_AND_MODELS.md), [human review and learning](../docs/LEARNING_AND_DEPLOYMENT.md), [replacement tools](../docs/Replacement-Tools.md), [CPU Docker](../docs/CPU_DOCKER.md), [design review](../docs/DESIGN_REVIEW_2026-10-27.md), and [third-party notices](../THIRD_PARTY_NOTICES.md).

The external course brief remains a separate instructor-owned reference. Private reports, access credentials, raw datasets, internal working notes and archived drafts are excluded.
