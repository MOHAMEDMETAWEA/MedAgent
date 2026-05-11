@echo off
TITLE MedAgent - Full System Launcher
COLOR 0A
ECHO Checking system requirements...

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    ECHO [ERROR] Python not found in PATH. Please install Python to run the AI engine.
    pause
    exit /b
)

:: Check for .NET
dotnet --version >nul 2>&1
if %errorlevel% neq 0 (
    ECHO [ERROR] .NET SDK not found in PATH. Please install .NET to run the Backend.
    pause
    exit /b
)

:: Check for Node/NPM
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    ECHO [ERROR] Node.js/NPM not found in PATH. Please install Node.js to run the Frontend.
    pause
    exit /b
)

ECHO Cleaning up old processes...
taskkill /F /IM "python.exe" /T >nul 2>&1
taskkill /F /IM "dotnet.exe" /T >nul 2>&1
taskkill /F /IM "node.exe" /T >nul 2>&1

ECHO All requirements met. Starting MedAgent Full System...

ECHO ===================================================
ECHO [1/3] Starting Agentic AI Engine (Python/FastAPI)...
ECHO Port API: 8000, Streamlit: 8501
start "Agentic AI Engine" cmd /k "cd /d "%~dp0Agentic AI engine" && python run_system.py"

ECHO [2/3] Starting .NET Backend API (Standard Auth)...
ECHO Port: 10000
start ".NET Backend API" cmd /k "cd /d "%~dp0fullstack\backend\MedAgent.Api\src\MedAgent.Api" && dotnet run"

ECHO [3/3] Starting React Vite Frontend...
ECHO Port: 5173
start "React Frontend" cmd /k "cd /d "%~dp0fullstack\frontend" && (if not exist node_modules npm install) && npm run dev"

ECHO ===================================================
ECHO All services launched. Monitor each window for specific errors.
ECHO - Frontend: http://localhost:5173
ECHO - Backend API: http://localhost:10000/swagger
ECHO - AI engine API: http://localhost:8000/docs
ECHO - AI engine Dashboard: http://localhost:8501
ECHO ===================================================
ECHO Press any key to close this launcher (servers will keep running).
pause
