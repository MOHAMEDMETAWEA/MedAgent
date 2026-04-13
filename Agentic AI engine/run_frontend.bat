@echo off
REM Run MedAgent web UI. Start the backend first (run_backend.bat).
cd /d "%~dp0"
if exist venv\Scripts\activate.bat call venv\Scripts\activate.bat
echo Starting MedAgent UI at http://localhost:8501 ...
streamlit run api/frontend.py --server.port 8501
pause
