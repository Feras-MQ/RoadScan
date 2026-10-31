# Exercise only pure configuration functions; never execute the launcher, Docker or credential creation.
$ErrorActionPreference = 'Stop'
$launcher = Join-Path (Split-Path $PSScriptRoot -Parent) 'Start-RoadScan.ps1'
$tokens = $null; $parseErrors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($launcher, [ref]$tokens, [ref]$parseErrors)
if ($parseErrors.Count) { throw 'Launcher failed PowerShell syntax validation.' }
foreach ($name in @('Read-LauncherSetting', 'Assert-LauncherProject')) {
    $definition = $ast.Find({param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq $name}, $true)
    if (-not $definition) { throw "Missing function: $name" }
    . ([scriptblock]::Create($definition.Extent.Text))
}
$fixture = [IO.Path]::GetTempFileName()
$original = $env:ROADSCAN_WITH_DETECTOR
$passed = 0
function Equal($actual, $expected) {
    if ($actual -cne $expected) { throw 'Unexpected launcher setting resolution.' }
    $script:passed++
}
function Reject([scriptblock]$operation) {
    $rejected = $false
    try { & $operation } catch { $rejected = $true }
    if (-not $rejected) { throw 'Ambiguous project selection was not blocked.' }
    $script:passed++
}
try {
    $env:ROADSCAN_WITH_DETECTOR = ''
    Equal (Read-LauncherSetting 'ROADSCAN_WITH_DETECTOR' $fixture '1') '1'
    Set-Content -LiteralPath $fixture -Value 'ROADSCAN_WITH_DETECTOR=0'
    Equal (Read-LauncherSetting 'ROADSCAN_WITH_DETECTOR' $fixture '1') '0'
    $env:ROADSCAN_WITH_DETECTOR = '1'
    Equal (Read-LauncherSetting 'ROADSCAN_WITH_DETECTOR' $fixture '1') '1'
    $env:ROADSCAN_WITH_DETECTOR = '0'
    Set-Content -LiteralPath $fixture -Value 'ROADSCAN_WITH_DETECTOR=1'
    Equal (Read-LauncherSetting 'ROADSCAN_WITH_DETECTOR' $fixture '1') '0'
    $env:ROADSCAN_WITH_DETECTOR = ''
    Set-Content -LiteralPath $fixture -Value 'ROADSCAN_WITH_DETECTOR="1" # CPU detector'
    Equal (Read-LauncherSetting 'ROADSCAN_WITH_DETECTOR' $fixture '1') '1'
    Add-Content -LiteralPath $fixture -Value 'ROADSCAN_WITH_DETECTOR=0'
    Equal (Read-LauncherSetting 'ROADSCAN_WITH_DETECTOR' $fixture '1') '0'
    Assert-LauncherProject 'roadscan' @() $false; $passed++
    Assert-LauncherProject 'roadscan' @('roadscan','roadscan') $false; $passed++
    Assert-LauncherProject 'existing-course' @('existing-course') $true; $passed++
    Assert-LauncherProject 'existing-course' @('roadscan','existing-course') $true; $passed++
    Reject { Assert-LauncherProject 'roadscan' @('existing-course') $false }
    Reject { Assert-LauncherProject 'new-name' @('existing-course') $true }
    Reject { Assert-LauncherProject 'roadscan' @('roadscan','existing-course') $false }
    Reject { Assert-LauncherProject '../wrong' @() $true }
    Write-Output "$passed launcher checks passed; no Docker, credentials or project data touched."
} finally {
    $env:ROADSCAN_WITH_DETECTOR = $original
    Remove-Item -LiteralPath $fixture
}
