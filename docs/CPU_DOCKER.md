# Run RoadScan on another computer

**Need:** Docker with Linux containers, an internet connection for the first build, and about 4 GB of Docker memory. No GPU or host Python is required. Keep at least 10 GB free for Docker images and builds; extra models need more space.

## Windows — easiest

1. Extract the **Ready-To-Run ZIP** into a normal folder.
2. Open Docker Desktop, then double-click **Start-RoadScan.cmd** inside `RoadScan`.
3. Open **http://127.0.0.1:8000** and paste the access token copied by the launcher.

The older `START_DOCKER_WINDOWS.cmd` now calls the same launcher. Existing `.env` settings are preserved. The portable package includes a baseline detector and a separate team-model ZIP; import that ZIP in Settings for the team detectors.

## macOS or Linux

Extract the portable ZIP, open Terminal in its `RoadScan` folder, and run:

```sh
docker run --rm --user "$(id -u):$(id -g)" --mount "type=bind,source=$PWD,target=/workspace" -w /workspace python:3.11-slim@sha256:e88e9763f943ec1834f992a4b51e0f24500486803e8bc534e5767af9ea65f6ce python tools/prepare_local_env.py
docker compose up --build -d
```

Open **http://127.0.0.1:8000**. Copy only the value after `ROADSCAN_API_KEY=` in your local `.env` into RoadScan's connection box; keep this file private. The setup helper preserves an existing `.env`, verifies a supplied baseline model against its recorded hash and enables the CPU detector build.

**Source-only download:** model weights are deliberately excluded. Run the same commands, then import a trusted team model in Settings; detection is unavailable until a model is installed. For a source-only Windows folder, use this first command in PowerShell, followed by `docker compose up --build -d`:

```powershell
docker run --rm --mount "type=bind,source=$($PWD.Path),target=/workspace" -w /workspace python:3.11-slim@sha256:e88e9763f943ec1834f992a4b51e0f24500486803e8bc534e5767af9ea65f6ce python tools/prepare_local_env.py
```

## Stop or restart

```sh
docker compose stop
docker compose start
```

Reports remain in the Docker `roadscan_data` volume. Do not remove that volume to update the app. Only localhost is exposed; remote phones/drones do not connect directly to this URL. Iriun/USB cameras must appear as a camera on the computer running the browser.

## What was verified

Release .2 already passed 217 backend baseline tests, 24 frontend tests and 10 English/Arabic responsive cases. The October 27 portability check separately exercises CPU dependencies and a synthetic report in a new isolated volume; see the delivery evidence for its recorded outcome.

Pinned base images and dependency indexes have Linux x86-64 and ARM64 candidates. This is not a claim of an actual fresh Mac, ARM or offline installation: those require the target hardware, and the initial build downloads dependencies.
