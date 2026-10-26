# RoadScan

Road inspection, live recognition and human-reviewed reporting by Feras Alyamani, Ahmed Salamah and Ahmed Alhejaili.

This private repository contains application source, tests and build configuration for release **2026-10-26.2**, with CPU setup updates from 27 October. It excludes access tokens, private reports, datasets and model weights.

## Run

Use [the CPU Docker guide](docs/CPU_DOCKER.md) on Windows, macOS or Linux. A source-only checkout needs a trusted model imported in Settings before detection is available; obtain the model package from the team. The first build needs internet access. Do not commit `.env` or model files.

## Features

- Photo batches, live camera recognition and every-decoded-frame video analysis.
- Human box correction and status review; a reviewer may choose a minority voting model.
- Reviewed-data export for separate training; corrections do not instantly retrain weights.
- Bilingual English/Arabic UI, heuristic repair priority and experimental duplicate matching.

## Evidence and limits

The verified application baseline passed 217 backend checks (1 optional skip), 24 frontend tests and 10 responsive cases. CPU setup adds three focused tests and a separate isolated Docker inference check. These are software checks, not field accuracy. Real Saudi test photos, duplicate calibration and repaired split evidence remain outstanding. Full submission documents and supplied weights are distributed separately by the team.

## Tests

Run `python -m pytest` in the configured development environment and `npm test` in `frontend` after installing its locked dependencies. `python tests/test_prepare_local_env.py` tests CPU setup using only Python's standard library. See [third-party notices](THIRD_PARTY_NOTICES.md).
