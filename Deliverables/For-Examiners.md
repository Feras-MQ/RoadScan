# RoadScan — demonstration and evidence

Team: Feras Alyamani, Ahmed Salamah, Ahmed Alhejaili. Prepared release: 2026-10-27.1.

Read the [30 October supplement](Submission-Audit-2026-10-30.md) with the dated report and refreshed 31 October deck: three additional experimental detectors are locally available, bringing the inventory to 22 unique weights. The baseline's published download and remaining per-weight conditions are in the [current matrix](Model-Release-Matrix-2026-10-30.md).

## Five-minute presentation

Use slides 1–7 for the main story and 8–12 for optional questions; see [Presentation-Guide.md](Presentation-Guide.md) for timings and [Speaker-Notes.txt](Speaker-Notes.txt) for the script.

The PDF stands alone if there is no live presentation. If the official ten-minute presentation/demo slot is used, expand the experiment appendix and add a rehearsed demonstration. Rehearse the actual camera and presentation files beforehand; native PowerPoint animation/playback is unverified and the delivered deck is static.

## Defensible answers

- **63.04% mAP50 / 33.01% mAP50–95:** team-reported labeled RDD holdout results; not official leaderboard scores or independently reproduced accuracy.
- **221 backend + 24 frontend tests passed; 67 browser checks passed:** software checks; one optional scikit-learn baseline test skipped because its dependency is absent from the app image.
- **0–100 priority:** transparent heuristic using class, image-relative area, count and confidence/review weight; not measured depth or certified engineering severity.
- **0.80 duplicate threshold:** experimental crop similarity within 50 m, not calibrated on real repeat-damage pairs.
- **Human learning loop:** review > approve > export > train separately > evaluate > import accepted weights.

## Files

- Docs/RoadScan-Project-Report.docx and .pdf: synchronized appendix content and current 18-page PDF; Word pagination remains unverified.
- Docs/RoadScan-Presentation.pptx and .pdf: slides.
- Docs/Submission-Readiness.md: mandatory evidence and hand-in checks.
- Models/Model-Inventory.csv: checkpoint identities and provenance.
- Validation-Status.md: verified checks and current limits.
- ../: application, tests and replacement research scripts.

The PDF is the current layout-checked reference. Word is installed, but its controls could not be targeted reliably and no connected document-control session was available; DOCX pagination remains unverified.
