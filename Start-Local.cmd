@echo off
cd /d "%~dp0"
rem Load the access key and settings from .env (Docker reads it by itself; this local start did not).
if exist ".env" for /f "usebackq eol=# tokens=1,* delims==" %%a in (".env") do set "%%a=%%b"
rem Same as Docker's PYTHONPATH: the bundled DINOv2 code (duplicate finder) lives in third_party.
set "PYTHONPATH=%~dp0;%~dp0third_party"
echo Starting RoadScan local server...
start http://127.0.0.1:8000/
"%~dp0venv\Scripts\python.exe" -m roadscan.web_server
pause
