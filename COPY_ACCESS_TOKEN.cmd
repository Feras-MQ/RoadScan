@echo off
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Copy-RoadScan-Token.ps1" -NoBrowser
if errorlevel 1 pause
