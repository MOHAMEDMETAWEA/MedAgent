@echo off
REM Run MedAgent backend API. Use from project root.
cd /d "%~dp0"
if exist venv\Scripts\activate.bat call venv\Scripts\activate.bat
echo Starting MedAgent API at http://localhost:8000 ...
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
pause
