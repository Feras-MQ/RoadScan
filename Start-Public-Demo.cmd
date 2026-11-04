@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0demo\Start-Demo.ps1"
if errorlevel 1 pause
