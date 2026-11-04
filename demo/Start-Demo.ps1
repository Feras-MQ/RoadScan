param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
Push-Location $root
try {
    & docker info --format '{{.OSType}}' | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Start Docker Desktop with Linux containers, then run this launcher again.' }
    $envPath = Join-Path $PSScriptRoot '.env'
    if (-not (Test-Path -LiteralPath $envPath)) {
        $bytes = New-Object byte[] 32
        $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
        try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
        $token = [Convert]::ToBase64String($bytes)
        $stream = [System.IO.File]::Open($envPath, [System.IO.FileMode]::CreateNew)
        try {
            $contents = [Text.Encoding]::ASCII.GetBytes("ROADSCAN_API_KEY=$token`n")
            $stream.Write($contents, 0, $contents.Length)
        } finally { $stream.Dispose() }
    }
    & docker compose --env-file demo/.env -p roadscan-public-demo -f compose.demo.yaml up --build -d --wait roadscan
    if ($LASTEXITCODE -ne 0) { throw 'Demo did not become ready. Existing data is preserved; inspect Docker output above.' }
    $line = Get-Content -LiteralPath $envPath | Where-Object { $_ -match '^ROADSCAN_API_KEY=' } | Select-Object -First 1
    if (-not $line) { throw 'demo/.env has no ROADSCAN_API_KEY. Keep existing data and correct this local file.' }
    $token = $line.Substring('ROADSCAN_API_KEY='.Length)
    if ($env:ROADSCAN_API_KEY) { $token = $env:ROADSCAN_API_KEY }
    Set-Clipboard -Value $token
    Write-Host 'Public synthetic demo ready at http://127.0.0.1:18010. Token copied; paste it into Access token and Connect.'
    Write-Host '14 illustrative reports, 10 simulated pins. No trained model outputs. See demo/README.md.'
    if (-not $NoBrowser) { Start-Process 'http://127.0.0.1:18010' }
} finally { Pop-Location }
