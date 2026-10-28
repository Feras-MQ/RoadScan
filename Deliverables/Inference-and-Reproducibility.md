# Reproduce inference without retraining

Use the [root quick start](../README.md#quick-start--windows) to build the pinned Docker environment, then install and activate a trusted compatible checkpoint through the model library. The source download alone does not contain trained road weights; [public road-detector downloads](Models.md) remain pending. The available DINOv2 and stock COCO downloads do not replace a road-trained detector.

The project already provides a standalone HTTP inference interface: **POST `/api/recognize?mode=detail`**. It accepts raw JPEG, PNG or WebP bytes, returns boxes/classes/confidences and model information, and does not create a saved report. This endpoint has a **2 MiB / 2 megapixel** frame limit; it is separate from the larger photo-upload workflow.

From the repository folder in PowerShell, after setup and model activation:

```powershell
$roadscanKeyLine = Get-Content .env | Where-Object { $_ -match '^ROADSCAN_API_KEY=' } | Select-Object -First 1
if (-not $roadscanKeyLine) { throw 'Create the local environment using the setup guide first.' }
$roadscanToken = ($roadscanKeyLine -split '=', 2)[1].Trim().Trim('"').Trim("'")
$roadscanResult = Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8000/api/recognize?mode=detail' -Headers @{ 'X-API-Key' = $roadscanToken } -ContentType 'image/jpeg' -InFile '.\example-road.jpg'
if ($roadscanResult.state -ne 'completed' -or $roadscanResult.persisted -ne $false) { throw 'Inference did not complete; inspect the returned model state.' }
$roadscanResult | ConvertTo-Json -Depth 20 | Set-Content -Encoding utf8 'inference-result.json'
Remove-Variable roadscanToken
```

Use your own suitably sized image and its matching content type. HTTP 200 alone does not mean successful detection: missing, busy and failed models have explicit non-completed states. A completed result with no boxes is different from a model failure. Keep `.env` and access tokens private.

For a saved result and human review, use the photo-upload screen instead. Live camera preview samples frames; sequential uploaded-video analysis is a separate workflow.

## Runtime and model provenance

- Docker pins base images and Python CPU dependency constraints; frontend installation uses `npm ci` and `package-lock.json`. Use this documented Docker path for reproducibility; a bare `pip install -r requirements.txt` does not reproduce the locked runtime.
- [Model inventory](public-model-inventory.json) maps SHA-256, size, task, origin and proposed release filename. Exact classes/configuration and original experiments are described in [team model results](Team-Models-and-Results.md); missing training provenance is stated explicitly.
- Preserve the supplied baseline and improved checkpoints by hash. Do not relabel a checkpoint as `last`, fabricate missing training history or imply that a classifier/embedding model is a detector.
- [Validation status](Validation-Status.md) distinguishes tested software behavior, supplied model results and the pending common-set benchmark. Fresh-clone acceptance with downloaded release weights remains pending.

Existing tests in `tests/test_live_recognition.py` cover raw-frame recognition, permissions/rejected frames, non-success states and the absence of saved reports/files/audit rows. No duplicate inference implementation is needed.
