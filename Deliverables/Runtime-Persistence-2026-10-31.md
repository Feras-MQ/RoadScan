# Runtime persistence — 31 October 2026

**Completed: RoadScan is healthy and running r5 from its rebuilt image at http://127.0.0.1:8000/.** Its 19 production reports, nine stopped-demo reports, database contents, model catalog, uploaded images and runtime settings were preserved.

## What is now ready

- A genuine source build completed successfully using the existing Dockerfile, with detector support explicitly enabled. This is not a snapshot of a running container.
- Image: `roadscan-roadscan:2026-10-31-r5`
- Image identity: `sha256:ec799ef8aa5f4ab4ce966dac70d066033e7973582687ab7e948972276a6dcc90`
- A read-only, network-disabled integrity check exited successfully with no production volumes mounted. It verified the API hash, map interface, corrected preview CSS, PyTorch 2.11.0+cpu and Ultralytics 8.4.175.
- All **116 backend regression tests passed inside the new image**, with one dependency deprecation warning and no skips.
- Only the production container was replaced under the existing deployment approval. Existing volumes, backups, old images and unrelated containers were retained. The Compose image tag now points to the rebuilt r5 image.
- The old runtime also has a private local rollback snapshot. It includes runtime configuration and must not be published. It is distinct from the clean source-built production image.

## Important distinction

**Normal restart:** r5 now belongs to the image itself, rather than depending on edits to the old container.

**Container recreation:** completed and verified. The replacement container uses image `sha256:ec799ef8aa5f4ab4ce966dac70d066033e7973582687ab7e948972276a6dcc90`; its original frontend/API are r5. The image was built from the source Dockerfile with detector support enabled and an explicit `io.roadscan.release=2026-10-31.r5` label override; it was not created by committing the old container.

## Preservation and recognition evidence

1. The project remains `roadscan`, with the same named data volume and read-only models mount. Runtime environment, resource settings, ports, restart policy and health check matched the previous container.
2. The saved model checksum now matches the previously running value, and the saved detector build setting is `1`. Existing credentials and all other settings were retained; the original configuration was privately backed up. Main remains the selected model.
3. The real recognition endpoint successfully analyzed one synthetic 640 × 360 frame using `main_yolo26s_1024.pt@9f940caa9222`; it returned `persisted=false`. No report was created. This verifies detector operation, not accuracy or live-camera performance; the single observed processing time is not a benchmark.
4. Before/after production database dumps and file hashes matched exactly, including uploaded images and model-library files. Production still has 19 reports; the stopped nine-report demo container was untouched. Health is confirmed after recreation.

The earlier no-deletion wording was clarified as preservation of data, backups, old images and unrelated containers, not a new prohibition on the already-approved production replacement. No additional owner approval was requested.

Detailed private receipts and stopped-service backups remain on the owner's laptop and are excluded from the public source ZIP. Full anonymous re-download verification of the prior publication remains incomplete because of network/certificate failures; certificate checks were not weakened. No new accuracy evaluation, fresh-machine installation or physical camera/drone test is claimed.
