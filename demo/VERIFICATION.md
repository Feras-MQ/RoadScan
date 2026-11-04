# Public demo verification - 4 November 2026

Checked against application commit `0964ed24ba1c3dd483377e910c8d26b5637768d9` plus this demo package, in a fresh clone and a new isolated Docker volume. The original laptop kit, database, models, submission files and videos were not changed.

## Measured lightweight workflow

Windows laptop: Intel Core i5-1135G7 (4 cores / 8 threads), approximately 8 GB RAM; Docker Desktop Linux engine 29.8.2, with about 3.7 GiB available to Docker. No GPU was used.

| Check | Observed result |
| --- | --- |
| First package build, seed and healthy startup | 75.59 seconds; Docker base images were already cached, application dependencies downloaded |
| Stop then restart, including health check | 13.21 seconds |
| Browser navigation to connected overview | 386 ms, local headless Chrome |
| Statistics API, 20 sequential local requests | Median 8 ms; p95 18 ms |
| Idle application container | About 55.22 MiB RAM; one sample, excludes browser and Docker engine |
| Lightweight image size | 329,456,091 bytes locally; not a download-size promise |

These measurements are for the **model-free workflow demo**, not ML inference. First use on a new computer also requires Docker installation/base-image downloads. Network speed and hardware change timings. Repeat starts need no dependency downloads when the image is unchanged. Stop/start measurements used the documented Compose commands; reopening the Windows launcher also checks the build cache.

## Optional baseline CPU measurement

Separately ran the already available original YOLO11n baseline in the laptop's existing detector image for application commit `0964ed2`. The disposable container had 2 CPUs, 2 inference threads, a 1.5 GB memory limit and no network. The checkpoint and one local demonstration photo were mounted read-only; that photo is not published here.

- Checkpoint SHA256: `2bb146ad53a3ddd149320aae3be67b2b1d50ccf0fdbc909edd749538055a2551`, 5,536,234 bytes.
- One 565 x 353 image, inference size 640, confidence 0.25: model loading 3.2581 s plus first prediction 2.3627 s (5.6209 s combined).
- Five warm predictions: 0.1141 / 0.0618 / 0.0442 / 0.0481 / 0.0460 s; median 0.0481 s. All completed, with one detection each.
- Peak process RSS about 432.4 MiB; entire disposable Docker command 8.213 s.

This is a single-image timing check, not accuracy evidence or a camera/video frame-rate claim. It excludes UI upload time and first-time installation/downloads, and does not verify a fresh detector build. Larger models and images can be substantially slower. The lightweight default still needs the optional detector setup before inference.

## Passed checks

- Fresh isolated Docker startup through `demo/Start-Demo.ps1 -NoBrowser`; generated private token, initialized separate volume, healthy service at port 18010.
- 25 backend checks: public demo, workflow, map pins, review API and database roundtrip. One upstream Starlette deprecation warning; no failures.
- 56 existing frontend tests; TypeScript and Vite production build passed.
- Four focused seed tests included in the backend count: report/map/image API and saving a review; restart preserving files and edits byte-for-byte; rejection of existing/partial workspaces; rejection of a root directory.
- Headless browser: connected overview, 14 reports, 10 simulated pins, zero recorded pins, image review, save/reload/persistence and restoring the original note, Arabic layout at 390 px; no page errors.
- Visual inspection of English review and Arabic mobile screenshots; screenshots retained locally as test evidence, not copied from the private demo kit.
- Independent code review found and corrected two documentation mismatches (empty annotations and exact map controls). This was an agent review, not a Gemini review; Gemini was unavailable in this environment.
- Proposed public files checked for private paths, credential-like values and media provenance. `demo/.env` is Git-ignored and excluded. Raw database, original media, backups, caches and source models were not copied into this package.

## Limits

No fresh second physical computer, macOS/ARM system, offline first installation, physical camera/drone or field accuracy validation was performed. The optional detector build from a fresh download and its model import path were not exercised by the lightweight checks above. Online map tiles were not loaded in this browser check; the simulated coordinate diagram and report list were checked. Original photos/video remain unpublished pending redistribution permission; two model binaries remain unavailable pending source confirmation. These omissions do not prevent the lightweight synthetic workflow demo from starting.
