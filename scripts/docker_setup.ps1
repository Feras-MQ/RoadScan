$ErrorActionPreference = 'Stop'
if (Test-Path .env) { Write-Host 'Existing .env preserved.'; exit 0 }
$key = python -c 'import secrets;print(secrets.token_urlsafe(32))' 2>$null
if (-not $key) {
  $buffer = New-Object byte[] 32
  [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($buffer)
  $key = [Convert]::ToBase64String($buffer).Replace('+','-').Replace('/','_').TrimEnd('=')
}
"ROADSCAN_API_KEY=$key" | Set-Content -Encoding ascii .env
Write-Host 'FIRST LAUNCH: Save this access key privately:' -ForegroundColor Cyan
Write-Host $key -ForegroundColor Yellow
try { Set-Clipboard -Value $key; Write-Host 'Access key copied to clipboard.' } catch {}
