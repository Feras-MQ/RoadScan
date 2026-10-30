# RoadScan validation status

Prepared 27 October 2026 for release 2026-10-27.1.

**30 October addendum:** the table below is the historical release baseline. The [current audit](Submission-Audit-2026-10-30.md) records 22 unique weights, four small CPU compatibility checks and browser verification of the three new experimental choices. No full benchmark, new accuracy measurement or fresh public-download acceptance is claimed.

| Area | Verified evidence | Limit |
|---|---|---|
| Application checks | 221 backend tests passed, one optional skip; 24 frontend tests and 67 browser checks passed | These are software checks, not model accuracy |
| Fresh local lifecycle | 19 checks covered setup, trusted-model import, inference, review, restart and saved-data preservation; two model fault checks passed | Tested locally; a fresh public clone with downloaded release weights is still pending |
| CPU portability | Isolated Linux x86-64 Docker inference and dependency checks passed | Fresh Mac/ARM setup and drone hardware were not tested |
| Report | PDF has 14 main pages and four appendix pages; editable report content and images were checked | Word pagination remains unverified; use the PDF for fixed layout |
| Presentation | Seven main slides plus four appendices; all 11 slide visuals checked | Static slides; no animation or native PowerPoint playback claim |
| Models | 19 unique checkpoints inventoried with hashes; supplied experiment results documented | Common-set full evaluation is pending; 20-image preflights are not an accuracy ranking |
| Field validation | Collection and labeling guidance is supplied | Genuine labeled Saudi road photos and repeat-damage pairs still need collection |

The five-minute main presentation follows the team's requested format. The official longer presentation/demo slot can use the optional appendix and a rehearsed demonstration.

Reported model scores come from the supplied experiment records and their original splits. Imported checkpoints have incomplete training-overlap provenance; a shared evaluation set must not be described as independently held out for every imported model without that evidence. Classification, object detection and embedding retrieval require separate metrics.

Human review produces approved examples for a separate train/evaluate/import cycle. It does not change weights live. Model voting preserves individual predictions and allows a reviewer to choose a minority model; the majority is not automatically ground truth. Priority is a configurable review aid, not a calibrated physical severity measurement.
