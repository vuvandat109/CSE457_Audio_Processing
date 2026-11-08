@echo off
cd /d "%~dp0"
echo Starting Vietnamese ASR API...
python -m uvicorn main:app --host 0.0.0.0 --port 8000
pause