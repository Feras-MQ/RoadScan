# Run RoadScan on another computer

**Need:** Docker with Linux containers, an internet connection for the first build, and about 4 GB of Docker memory. No GPU or host Python is required. Keep at least 10 GB free for Docker images and builds; extra models need more space.

## New installation — public source download

**Already have RoadScan reports on this computer?** Read [existing-installation checks](#existing-installations-preserve-your-project-name) before starting; keep that installation's project name and volume.

1. Download or clone [the public repository](https://github.com/Feras-MQ/RoadScan) and open the folder containing `compose.yaml`.
2. Start Docker Desktop. On Windows, open PowerShell in that folder and run the commands below.
3. Open **http://127.0.0.1:8000**, paste the token copied by `COPY_ACCESS_TOKEN.cmd`, then select **Connect**.

```powershell
docker run --rm --mount "type=bind,source=$($PWD.Path),target=/workspace" -w /workspace python:3.11-slim@sha256:e88e9763f943ec1834f992a4b51e0f24500486803e8bc534e5767af9ea65f6ce python tools/prepare_local_env.py
docker compose -p roadscan up --build -d
.\COPY_ACCESS_TOKEN.cmd
```

Source downloads exclude weights: download [Main or the baseline](Models.md), verify its SHA256, then **Settings → Your model library → Browse models → Use model → verify Active**. Import alone does not activate it. CPU support defaults on in the Windows launcher; explicit `ROADSCAN_WITH_DETECTOR=0` or `1` is preserved (process environment first, then `.env`). The setup helper also preserves an existing `.env`; if it explicitly disables detection, change that setting deliberately before rebuilding to use a detector.

## macOS or Linux

For a new source installation, open Terminal in the folder containing `compose.yaml` and run:

```sh
docker run --rm --user "$(id -u):$(id -g)" --mount "type=bind,source=$PWD,target=/workspace" -w /workspace python:3.11-slim@sha256:e88e9763f943ec1834f992a4b51e0f24500486803e8bc534e5767af9ea65f6ce python tools/prepare_local_env.py
docker compose -p roadscan up --build -d
```

Open **http://127.0.0.1:8000**. Copy only the value after `ROADSCAN_API_KEY=` in your local `.env` into RoadScan's connection box; keep this file private. The setup helper preserves an existing `.env`, verifies a supplied baseline model against its recorded hash and enables the CPU detector build.

## Existing installations: preserve your project name

The examples use the explicit project name `roadscan`, matching the launcher. Older plain `docker compose` commands may have used the folder name instead. **Do not switch names to fix missing reports**: a different name can select a different data volume. Identify existing names with these read-only commands:

```sh
docker ps -a --filter label=com.docker.compose.service=roadscan --format '{{.Label `com.docker.compose.project`}}'
docker volume ls --filter label=com.docker.compose.volume=roadscan_data --format '{{.Label `com.docker.compose.project`}}'
```

Keep the intended existing name: replace `roadscan` in every `-p roadscan` command with that name, or run `powershell -File .\Start-RoadScan.ps1 -ComposeProject existing-name`. The launcher also respects `COMPOSE_PROJECT_NAME` in the process environment or `.env`. It stops if the selected name would bypass existing RoadScan data or if multiple existing names require an explicit choice. It does not rename, migrate or remove volumes. If unsure which name contains your reports, stop and inspect before starting another installation.

## Optional local portable bundle

Only if the team already supplied `RoadScan-Ready-To-Run-2026-10-27.1.zip`: extract it, open its `RoadScan` folder and use **Start-RoadScan.cmd**. That dated local bundle includes a baseline and may contain an older launcher; use its original project name. It is **not a published GitHub download** and is not required for the source path above. The legacy `START_DOCKER_WINDOWS.cmd` in current source forwards to the current launcher.

## Stop or restart

```sh
docker compose -p roadscan stop
docker compose -p roadscan start
```

Use your existing project name if it differs. Reports remain in that project's `roadscan_data` volume (normally `<project>_roadscan_data`). Do not remove it to update the app. Only localhost is exposed; remote phones/drones do not connect directly to this URL. Iriun/USB cameras must appear as a camera on the computer running the browser.

## What was verified

Release .2 already passed 217 backend baseline tests, 24 frontend tests and 10 English/Arabic responsive cases. The October 27 portability check separately exercises CPU dependencies and a synthetic report in a new isolated volume; see the delivery evidence for its recorded outcome.

Pinned base images and dependency indexes have Linux x86-64 and ARM64 candidates. This is not a claim of an actual fresh Mac, ARM or offline installation: those require the target hardware, and the initial build downloads dependencies.
