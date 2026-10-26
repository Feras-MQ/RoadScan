[CmdletBinding()]
param([string]$ProjectPath,[switch]$NoBrowser)
$ErrorActionPreference='Stop'
if(-not $ProjectPath){
    foreach($candidate in @($PSScriptRoot,'C:\Users\Feras Alyamani\Desktop\CAPSTONE\RoadScan_Rebuilt_Source_v1\RoadScan')){
        if(Test-Path -LiteralPath (Join-Path $candidate '.env') -PathType Leaf){$ProjectPath=$candidate;break}
    }
}
if(-not $ProjectPath){throw 'Run the real RoadScan launcher once, then copy its access key.'}
$config=Join-Path $ProjectPath '.env'
$line=Get-Content -LiteralPath $config | Where-Object {$_ -match '^\s*ROADSCAN_API_KEY\s*='} | Select-Object -First 1
if(-not $line){throw 'The real workspace has no saved access key.'}
$accessKey=($line -split '=',2)[1].Trim().Trim('"').Trim("'")
if(-not $accessKey){throw 'The saved access key is empty.'}
Set-Clipboard -Value $accessKey
Write-Host 'Real workspace token copied. Paste it into Access token at http://127.0.0.1:8000/ .'
Write-Host 'The separate presentation workspace at port 18004 connects automatically.'
if(-not $NoBrowser){Start-Process 'http://127.0.0.1:8000/'}

