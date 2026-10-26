[CmdletBinding()]
param([string]$ProjectPath, [switch]$CheckOnly, [switch]$NoBrowser, [switch]$CopyAccessKey, [switch]$Rebuild)
$ErrorActionPreference = 'Stop'

function Find-Docker {
    $command = Get-Command docker -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    foreach ($candidate in @(
        (Join-Path $env:LOCALAPPDATA 'Programs\DockerDesktop\resources\bin\docker.exe'),
        'C:\Program Files\Docker\Docker\resources\bin\docker.exe'
    )) { if (Test-Path -LiteralPath $candidate -PathType Leaf) { return $candidate } }
    throw 'Docker Desktop is required. Install it from https://www.docker.com/products/docker-desktop/ and start it once.'
}

function Test-DockerEngine {
    $savedPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & $docker info --format '{{.OSType}}' 2>$null | Out-Null
        return $LASTEXITCODE -eq 0
    } finally { $ErrorActionPreference = $savedPreference }
}

if (-not $ProjectPath) {
    foreach ($candidate in @($PSScriptRoot, (Join-Path $PSScriptRoot 'RoadScan'), 'C:\Users\Feras Alyamani\Desktop\CAPSTONE\RoadScan_Rebuilt_Source_v1\RoadScan')) {
        if (Test-Path -LiteralPath (Join-Path $candidate 'compose.yaml') -PathType Leaf) { $ProjectPath = $candidate; break }
    }
}
if (-not $ProjectPath) { throw 'Extract the verified source ZIP beside this launcher, or run with -ProjectPath pointing to RoadScan.' }
$project = (Resolve-Path -LiteralPath $ProjectPath).Path
if (-not (Test-Path -LiteralPath (Join-Path $project 'compose.yaml') -PathType Leaf)) { throw 'The selected folder has no RoadScan compose.yaml.' }
$docker = Find-Docker
$compose = @('compose', '--project-name', 'roadscan', '--project-directory', $project, '-f', (Join-Path $project 'compose.yaml'))

if ($CheckOnly) {
    Write-Host "RoadScan folder: $project"
    if (-not (Test-DockerEngine)) { throw 'Docker is not running.' }
    $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/health' -TimeoutSec 5
    Write-Host "Local app: $($health.status). Detector: $($health.model)."
    Write-Host 'Read-only check passed. No files, tokens or containers changed.'
    exit 0
}

if (-not (Test-DockerEngine)) {
    $desktop = Join-Path $env:LOCALAPPDATA 'Programs\DockerDesktop\Docker Desktop.exe'
    if (-not (Test-Path -LiteralPath $desktop)) { $desktop = 'C:\Program Files\Docker\Docker\Docker Desktop.exe' }
    if (-not (Test-Path -LiteralPath $desktop)) { throw 'Open Docker Desktop, then launch RoadScan again.' }
    Start-Process -FilePath $desktop -WindowStyle Hidden
    Write-Host 'Starting Docker Desktop. This can take a minute.'
    $available = $false
    for ($attempt = 0; $attempt -lt 90; $attempt++) {
        if (Test-DockerEngine) { $available = $true; break }
        Start-Sleep -Seconds 2
    }
    if (-not $available) { throw 'Docker did not become ready. Open Docker Desktop and check its status.' }
}

$envPath = Join-Path $project '.env'
if (-not (Test-Path -LiteralPath $envPath -PathType Leaf)) {
    $random = New-Object byte[] 32
    $generator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $generator.GetBytes($random) } finally { $generator.Dispose() }
    $newKey = [Convert]::ToBase64String($random).Replace('+','-').Replace('/','_').TrimEnd('=')
    [System.IO.File]::WriteAllText($envPath, "ROADSCAN_API_KEY=$newKey`n", [System.Text.Encoding]::ASCII)
    Write-Host 'Created a private local access key. It is stored in .env and is never printed.'
}

$modelRecord = Join-Path $project 'models\roadscan_model.json'
$withDetector = '0'
if (Test-Path -LiteralPath $modelRecord -PathType Leaf) {
    $record = Get-Content -LiteralPath $modelRecord -Raw | ConvertFrom-Json
    $confidence = 0.0
    if (-not [double]::TryParse([string]$record.confidence, [System.Globalization.NumberStyles]::Float, [System.Globalization.CultureInfo]::InvariantCulture, [ref]$confidence) -or [double]::IsNaN($confidence) -or [double]::IsInfinity($confidence) -or $confidence -lt 0 -or $confidence -gt 1) { throw 'The model confidence must be a finite number from 0 to 1.' }
    $weights = Join-Path $project 'models\roadscan_best.pt'
    if (-not (Test-Path -LiteralPath $weights -PathType Leaf)) { throw 'The recorded detector checkpoint is missing. Restore the model package before starting.' }
    $hasher = [System.Security.Cryptography.SHA256]::Create()
    $weightStream = [System.IO.File]::OpenRead($weights)
    try { $actualHash = [BitConverter]::ToString($hasher.ComputeHash($weightStream)).Replace('-','').ToLowerInvariant() }
    finally { $weightStream.Dispose(); $hasher.Dispose() }
    if ($actualHash -ne $record.sha256) { throw 'The detector checkpoint does not match its recorded hash. It will not be loaded.' }
    $env:ROADSCAN_YOLO_WEIGHTS = '/models/roadscan_best.pt'
    $env:ROADSCAN_YOLO_SHA256 = $actualHash
    $env:ROADSCAN_CONFIDENCE = $confidence.ToString([System.Globalization.CultureInfo]::InvariantCulture)
    if ($record.status -eq 'experimental') { Write-Host 'Experimental models: check the documented validation results. Review every report; no boxes does not mean no damage.' }
    $withDetector = '1'
}
$env:ROADSCAN_WITH_DETECTOR = $withDetector
$existingImage = & $docker image ls --filter reference=roadscan-roadscan --format '{{.ID}}'
$feature = ''
$imageRelease = ''
$releaseFile = Join-Path $project 'ROADSCAN_RELEASE'
$expectedRelease = if (Test-Path -LiteralPath $releaseFile) { (Get-Content -LiteralPath $releaseFile -Raw).Trim() } else { '' }
if ($existingImage) {
    $labels = (& $docker image inspect roadscan-roadscan --format '{{json .Config.Labels}}') | ConvertFrom-Json
    $feature = $labels.'io.roadscan.detector'
    $imageRelease = $labels.'io.roadscan.release'
}
$build = $Rebuild -or -not $existingImage -or ($withDetector -eq '1' -and [string]$feature -ne '1') -or ($expectedRelease -and $expectedRelease -ne $imageRelease)
if ($build) {
    Write-Host 'Preparing RoadScan. The first build needs an internet connection; later launches reuse it.'
    & $docker @compose build roadscan
    if ($LASTEXITCODE -ne 0) { throw 'RoadScan build failed. Your saved data was not removed.' }
}
& $docker @compose up -d --no-build roadscan
if ($LASTEXITCODE -ne 0) { throw 'RoadScan could not start. Your saved data was not removed.' }
$ready = $false
for ($attempt = 0; $attempt -lt 60; $attempt++) {
    try {
        $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/health' -TimeoutSec 3
        if ($health.status -eq 'ok') { $ready = $true; break }
    } catch {}
    Start-Sleep -Seconds 1
}
if (-not $ready) { throw 'The app did not become ready. Check Docker Desktop; saved reports remain in its data volume.' }
if ($CopyAccessKey) {
    $keyLine = Get-Content -LiteralPath $envPath | Where-Object { $_ -match '^\s*ROADSCAN_API_KEY\s*=' } | Select-Object -First 1
    if ($keyLine) {
        $accessKey = ($keyLine -split '=', 2)[1].Trim().Trim('"').Trim("'")
        Set-Clipboard -Value $accessKey
        Write-Host 'Access key copied to your clipboard. Paste it into Connect if asked. Keep it private.'
    }
}
Write-Host 'RoadScan is ready at http://127.0.0.1:8000/ - saved reports are preserved.'
Write-Host "Detector status: $($health.model). Human review is required."
if (-not $NoBrowser) { Start-Process 'http://127.0.0.1:8000/' }
