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
ECHO Starting Agentic AI Engine (Python)...
start "Agentic AI Engine" cmd /k "cd /d "%~dp0Agentic AI engine" && python run_system.py"

ECHO Starting .NET Backend API...
start ".NET Backend API" cmd /k "cd /d "%~dp0fullstack\backend\MedAgent.Api\src\MedAgent.Api" && dotnet run"

ECHO Starting React Vite Frontend...
start "React Frontend" cmd /k "cd /d "%~dp0fullstack\frontend" && npm run dev"
ECHO ===================================================
ECHO All services launched. Monitor each window for specific errors.
ECHO Press any key to close this launcher (servers will keep running).
pause
