# RoadScan

Road inspection, live recognition and human-reviewed reporting by Feras Alyamani, Ahmed Salamah and Ahmed Alhejaili.

This private repository contains application source, tests and build configuration for release **2026-10-27.1**, including the 27 October review-workflow update. It excludes access tokens, private reports, datasets and model weights.

## Run

Use [the CPU Docker guide](docs/CPU_DOCKER.md) on Windows, macOS or Linux. A source-only checkout needs a trusted model imported in Settings before detection is available; obtain the model package from the team. The first build needs internet access. Do not commit `.env` or model files.

## Features

- Photo batches, live camera recognition and every-decoded-frame video analysis.
- Human box correction and status review; a reviewer may choose a minority voting model.
- Reviewed-data export for separate training; corrections do not instantly retrain weights.
- Bilingual English/Arabic UI, heuristic repair priority and experimental duplicate matching.

## Evidence and limits

This release passed 221 backend tests (1 optional skip), 24 frontend tests and 67 browser checks: 17 interaction checks, 40 EN/AR responsive cases and 10 final narrow-screen rechecks. The TypeScript/Vite build passed. The earlier CPU Docker baseline has a separate inference proof; fresh Mac/ARM installation remains unverified. See [the design and workflow evidence](docs/DESIGN_REVIEW_2026-10-27.md). These are software checks, not field accuracy. Real Saudi test photos, duplicate calibration and repaired split evidence remain outstanding. Full submission documents and supplied weights are distributed separately by the team.

## Tests

Run `python -m pytest` in the configured development environment and `npm test` in `frontend` after installing its locked dependencies. `python tests/test_prepare_local_env.py` tests CPU setup using only Python's standard library. See [third-party notices](THIRD_PARTY_NOTICES.md).
