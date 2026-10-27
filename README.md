# RoadScan

Road inspection, live recognition and human-reviewed reporting by Feras Alyamani, Ahmed Salamah and Ahmed Alhejaili.

Release **2026-10-27.1**. This private source repository excludes access tokens, private reports, datasets and model weights; full submission documents and model artifacts are supplied separately by the team.

## Quick start — Windows

**RoadScan runs the website, API and CPU detector together in Docker.** You do not need a GPU, Python or Node installed on your computer.

**Before starting:** open Docker Desktop with **Linux containers**, allow about **4 GB of Docker memory** and keep **10 GB free**; the first build needs internet and can take several minutes.

### 1. Get the project

- **GitHub:** accept the repository invitation while signed in to the invited account, then use **Code > Download ZIP** and extract it, or run the commands below if Git is installed.
- **Ready-To-Run bundle:** ask the team for `RoadScan-Ready-To-Run-2026-10-27.1.zip`, extract it and open its `RoadScan` folder; this bundle includes a baseline model, unlike GitHub.

```powershell
git clone https://github.com/Feras-MQ/RoadScan.git
cd RoadScan
```

This repository is private: a 404 or “Repository not found” usually means the invitation has not been accepted or you are signed in to a different account.

### 2. Start it

**Ready-To-Run bundle:** double-click **Start-RoadScan.cmd** inside `RoadScan`; it starts the app and copies your local access token. Continue to step 3.

**GitHub source:** open PowerShell in the extracted/cloned folder that contains `compose.yaml`, then paste these commands:

```powershell
docker run --rm --mount "type=bind,source=$($PWD.Path),target=/workspace" -w /workspace python:3.11-slim@sha256:e88e9763f943ec1834f992a4b51e0f24500486803e8bc534e5767af9ea65f6ce python tools/prepare_local_env.py
docker compose up --build -d
.\COPY_ACCESS_TOKEN.cmd
```

Use these commands for a source-only download: the double-click launcher expects bundled baseline-model metadata to enable detection. The helper creates a private `.env`, enables the CPU detector build and preserves an existing `.env`; it never prints your token.

### 3. Open and connect

Open **http://127.0.0.1:8000**, paste the copied token into **Access token**, and select **Connect**; run **COPY_ACCESS_TOKEN.cmd** again whenever you need to copy it.

For a GitHub download, install a model next: **Settings > Your model library > Browse models** (or drag a file) > choose a trusted team `.pt` or `.zip` > **Use model** > check **Active**. Importing alone does not activate a model.

**Weights are not on GitHub.** Obtain them separately from the team: a trusted checkpoint or `RoadScan-Team-Results-2026-10-24.zip`; the latter is also included under `models` in the Ready-To-Run bundle. No public model-download link is supplied here, and no paid inference API is required.

### 4. Confirm it works

```powershell
docker compose ps
Invoke-RestMethod http://127.0.0.1:8000/api/health | Select-Object status, model, model_reason
```

Expect **status = ok** and, after installing/activating a model, **model = configured**; `not_configured` is expected in a source-only workspace before model installation. Health alone does not prove detection works.

In **Overview**, choose **Browse files**, select one road photo and click **Analyze & create report**, then open its report and check **Analysis complete**; inspect the boxes, save a review note and refresh to confirm it remains saved. A photo with no detected damage can legitimately have zero boxes.

## Use the project

| Task | Where to go |
|---|---|
| Photo inspection | Overview > Browse files > choose photo > Analyze & create report > open the saved report |
| Camera / Iriun / USB | Live recognition > Camera > select your camera > Start live recognition |
| Every decoded video frame | Live recognition > Video - analyze every frame > choose the file > Analyze every frame; keep the tab visible |
| Human decision | Review queue > Inspect image > Check boxes > Save decision |
| Compare models | Saved report > Run model vote > choose agreement **or any individual model**, including a minority result > check boxes > Save review |
| Improve a later model | Save a Confirmed review > approve the training example > export from Learning; retraining and testing are separate steps |

## Stop and restart

From the **same project folder**:

```powershell
docker compose stop
docker compose start
```

For the Ready-To-Run bundle, you can also reopen **Start-RoadScan.cmd**. Reports and imported models stay in the Docker data volume; keep that volume and your `.env`, and do **not** use `docker compose down -v` to restart or update.

<details>
<summary><strong>Troubleshooting and advanced details</strong></summary>

| Problem | What to do |
|---|---|
| Docker command fails | Open Docker Desktop, wait until its engine is running and confirm Linux containers are selected |
| Port 8000 is already in use | Open the existing RoadScan first; stop only the conflicting workspace you own before starting another |
| Invalid token | Run COPY_ACCESS_TOKEN.cmd from this project's folder and paste again; the presentation demo on port 18004 is a separate prepared workspace |
| Model is not configured | Import a trusted team checkpoint and choose **Use model** |
| Model import says detector build is required | In this local `.env`, set `ROADSCAN_WITH_DETECTOR=1` without changing the token, then run `docker compose up --build -d`; the helper deliberately preserves existing settings |
| Imported file is rejected | Keep the rejection reason, use a supported trusted YOLO/RT-DETR `.pt` or model ZIP, and keep the previous working model |
| App is slow on a heavy model | Try the smaller supplied model for camera use; full video analysis deliberately waits for each frame's inference |
| Camera is missing | Allow browser camera access and check that Iriun/USB appears as a camera on this computer |
| Old screen after an update | Refresh the page once |

Logs: `docker compose logs --tail 50 roadscan` (inspect locally; redact sensitive content before sharing).

**macOS/Linux:** use the separate [CPU Docker guide](docs/CPU_DOCKER.md); physical Mac/ARM installation remains unverified. The Windows/Docker path and isolated Linux x86-64 CPU inference have been checked; this is not a claim about every computer.

**Location and drones:** localhost is this computer only; a remote phone or drone cannot connect directly to that address. Iriun/USB capture and imported recordings are supported inputs; direct drone integration and physical drone testing remain future work.

**Project map:** `frontend` = interface, `roadscan` = API/inference/review, `tests` = software checks, `tools` = setup helpers, `docs` = detailed guides, `models` = separately supplied weights. The app runs as one Docker service; you do not need to start the frontend separately.

Detailed guides: [live recognition and models](docs/LIVE_AND_MODELS.md), [learning and deployment](docs/LEARNING_AND_DEPLOYMENT.md), [replacement research tools](docs/Replacement-Tools.md), [third-party notices](THIRD_PARTY_NOTICES.md).

</details>

## Features

- Photo batches, live camera recognition and every-decoded-frame video analysis.
- Human box correction and status review; a reviewer may choose a minority voting model.
- Reviewed-data export for separate training; corrections do not instantly retrain weights.
- Bilingual English/Arabic UI, heuristic repair priority and experimental duplicate matching.

## Evidence and limits

This release passed 221 backend tests (1 optional skip), 24 frontend tests and 67 browser checks: 17 interaction checks, 40 EN/AR responsive cases and 10 final narrow-screen rechecks. The TypeScript/Vite build passed. The earlier CPU Docker baseline has a separate inference proof; fresh Mac/ARM installation remains unverified. See [the design and workflow evidence](docs/DESIGN_REVIEW_2026-10-27.md). These are software checks, not field accuracy. Real Saudi test photos, duplicate calibration and repaired split evidence remain outstanding. Full submission documents and supplied weights are distributed separately by the team.

## Tests

Use a disposable development checkout with a scratch database and storage, never a private-report workspace: run `python -m pytest` in that configured environment and `npm test` in `frontend` after installing its locked dependencies. `python tests/test_prepare_local_env.py` tests CPU setup using only Python's standard library. See [third-party notices](THIRD_PARTY_NOTICES.md).
