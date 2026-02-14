@echo off
TITLE MEDagent Global System - Launching...
COLOR 0A
ECHO ==========================================================
ECHO       MEDAGENT GLOBAL SYSTEM - PRODUCTION STARTUP
ECHO ==========================================================
ECHO.
ECHO [1/3] Checking Environment...
IF NOT EXIST ".env" (
    ECHO [WARNING] .env file not found. System may fail authorization.
    ECHO Please copy .env.example to .env and set your keys.
    PAUSE
)

ECHO [2/3] Installing/Updating Requirements...
pip install -r requirements.txt > NUL 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO [ERROR] Failed to install requirements. Please run 'pip install -r requirements.txt' manually.
    PAUSE
    EXIT /B
)
ECHO [OK] Dependencies ready.

ECHO [3/3] Launching System (Backend API + Frontend UI)...
ECHO.
ECHO * Backend API will be available at http://localhost:8000
ECHO * Frontend UI will be available at http://localhost:8501
ECHO.
ECHO Press Ctrl+C to stop the servers.
ECHO.

python run_system.py

PAUSE
