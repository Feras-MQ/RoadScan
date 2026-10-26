@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-RoadScan.ps1" -CopyAccessKey
if errorlevel 1 pause
