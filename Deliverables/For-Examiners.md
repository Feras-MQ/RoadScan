# RoadScan demonstration and evidence

Team: Feras Alyamani, Ahmed Salamah, Ahmed Alhejaili. Submitted documents: 1 November 2026. Source snapshot: `58e7c3e494b5e1c5f2ca4d431b24d3f099003205`.

Start with the [25-page technical report](RoadScan-Project-Report.pdf) or its [editable DOCX](RoadScan-Project-Report.docx). These replace the previous current report. The [Arabic revision guide PDF](Revision/RoadScan-Arabic-Revision-Guide.pdf) and [DOCX](Revision/RoadScan-Arabic-Revision-Guide.docx) are supplementary study materials, not substitutes for the full report.

## Presentation and demonstration

The final course plan has nine main slides and three backups. The ten-minute slot includes 2.5 minutes of panel-chosen live input; see [the timing guide](Presentation-Guide.md) and [approved English speaking text](Speaker-Notes.txt). The final presentation files remain unpublished because two saved project prediction images lack confirmed public redistribution rights. The retained [31 October PDF](RoadScan-Presentation.pdf) and [PPTX](RoadScan-Presentation.pptx) are historical and do not match the final script.

## Evidence boundaries

- Main's 63.04% mAP50 and 33.01% mAP50–95 are supplied historical RDD results, with reported near-duplicate leakage; they are not independently reproduced field accuracy.
- Road fine-tune scores use a 343-frame selection set reused for checkpoint and threshold choices, with overlapping video groups. They do not support a common independent ranking against Main.
- Software test counts retain their dates, commits and scopes in the report. They do not establish deployment, camera performance or model accuracy.
- The 0–100 priority is a transparent heuristic. Crop similarity and its duplicate threshold remain uncalibrated on genuine repeat-damage pairs.
- Human review can approve examples for export; training, evaluation and accepted-model import remain separate operations.

## Supporting records

- [Publication record and hashes](Submission-2026-11-01.md) / [all deliverables](README.md).
- [Model inventory](public-model-inventory.json) and [organization](Model-Organization-2026-11-01.md): 22 verified identities and two separately peer-reported identities.
- [Model availability](Models.md), [trainer provenance](Trainer-Provenance-2026-10-31.md) and the [historical submission audit](Submission-Audit-2026-10-30.md).
- [Application source](../roadscan/), [tests](../tests/) and [research scripts](../tools/).

The report and guide binaries are unchanged from the submitted ZIP. Native Word/PowerPoint playback has not been newly tested during this publication pass. Finished videos and runtime data are unchanged.
