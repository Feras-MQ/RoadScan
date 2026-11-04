# Public RoadScan demo

Download the repository, then double-click **Start-Public-Demo.cmd** in its top-level folder on Windows. Start Docker Desktop with Linux containers first. The first build needs internet and several minutes; no host Python, Node or GPU is required.

The launcher opens **http://127.0.0.1:18010** and copies a newly generated local access token. Paste it into **Access token**, then **Connect**. Keep `demo/.env` private. This demo has its own Docker project, volume and port; it does not stop or modify your usual RoadScan installation.

## What you get

- 14 generated illustrative reports: 8 Needs Review, 4 Confirmed, 1 Assigned and 1 Resolved.
- 10 clearly labelled **simulated** Madinah pins and 4 reports without locations.
- Original schematic road illustrations generated locally by the seed script. There are no prefilled boxes or detector outputs; add your own practice annotations. These examples are not field evidence, captured road photos or an accuracy benchmark.
- A repeatable first-run seed. Starting again preserves your edits. The seed refuses an existing unmarked data directory, so it cannot silently replace real reports.
- [Model download links and availability](MODELS.md), including Main. Weights are separate downloads and are not installed automatically.

This is a **public synthetic counterpart** of the November 3 presentation workflow. The original laptop kit's photos/video were marked internal-only in its provenance records, so those files, their thumbnails, raw database, backups and exports are not included. The current laptop has 17 reports and 9 catalogued models, including additions after the original 14-report showcase; see the sanitized [inspection snapshot](laptop-snapshot.json). That metadata is not a backup of the original reports.

## Try the demo

1. Open **Overview** and **Review queue**; inspect a report. Its image and note explicitly identify it as synthetic.
2. Add practice annotations or save a note or decision. Refresh to check that it persists.
3. Open **Map & results > Simulated locations**. The coordinate diagram works offline; optionally choose **Load street map** for online tiles. All ten pins are staged public-road positions, not image-capture GPS or actual damage locations. Four reports intentionally have no location.
4. Explore the Confirmed, Assigned and Resolved examples. Training/export controls, where available, operate on synthetic demonstrations only; do not use these examples as a real training or evaluation set.

The lightweight default build has no detector installed: `model = not_configured` is expected. Existing reports and human review work without a model; new photo inference, live/video inference, model voting and DINO similarity require the optional detector build and trusted weights. Map tiles need internet.

## Optional real inference

Add this line to **demo/.env**, preserving its existing token:

```dotenv
ROADSCAN_DEMO_WITH_DETECTOR=1
```

Run the launcher again to rebuild the CPU detector image. This takes longer and requires more disk space/memory (allow at least 10 GB free disk and 4 GB Docker memory). Download a trusted checkpoint from [MODELS.md](MODELS.md), verify its SHA256, then use **Settings > Your model library > Browse models > Use model** and verify **Active**. Only process media you have permission to use. Synthetic illustrations are not suitable for judging detector accuracy.

## macOS/Linux or command-line Windows

Run commands from the repository root. The existing environment helper generates a random token without printing it and preserves any existing `demo/.env`.

macOS/Linux:

```sh
docker run --rm --user "$(id -u):$(id -g)" --mount "type=bind,source=$PWD,target=/workspace" -w /workspace/demo python:3.11-slim@sha256:e88e9763f943ec1834f992a4b51e0f24500486803e8bc534e5767af9ea65f6ce python /workspace/tools/prepare_local_env.py
docker compose --env-file demo/.env -p roadscan-public-demo -f compose.demo.yaml up --build -d --wait roadscan
```

Windows PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\demo\Start-Demo.ps1
```

For manual setup, open http://127.0.0.1:18010 and copy the value after `ROADSCAN_API_KEY=` from `demo/.env` into the connection box. The public demo uses `ROADSCAN_DEMO_WITH_DETECTOR` for its build; the ordinary helper's `ROADSCAN_WITH_DETECTOR` flag does not control this separate demo.

## Stop, resume and preserve data

```sh
docker compose --env-file demo/.env -p roadscan-public-demo -f compose.demo.yaml stop
docker compose --env-file demo/.env -p roadscan-public-demo -f compose.demo.yaml up -d --wait roadscan
```

Keep the same folder, token and project name. Data is in `roadscan-public-demo_public_demo_data`. Do not remove the volume to restart. If port 18010 is occupied, resolve that conflict before starting; the launcher does not stop other applications. If the seed refuses existing data, preserve it and inspect the volume instead of deleting it.

## Provenance and verification

The illustrative images are generated from drawing instructions in `seed_demo.py`, with no third-party photographs. Simulated road coordinates derive from [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), [Madinah map extract](https://api.openstreetmap.org/api/0.6/map?bbox=39.600,24.466,39.613,24.478); OpenStreetMap data is available under the ODbL. Repeated pins intentionally demonstrate reports at the same staged location. No real capture coordinates from the laptop are included.

See [VERIFICATION.md](VERIFICATION.md) for actual checks and limits. Neither this package nor a successful health check establishes real-road accuracy, physical camera behavior, external integrations or a fresh installation on every operating system.
