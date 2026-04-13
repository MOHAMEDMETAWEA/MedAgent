@echo off
TITLE MedAgent - Full System Launcher
COLOR 0A
ECHO Starting MedAgent Full System...

ECHO ===================================================
ECHO Starting Agentic AI Engine (Python)...
start "Agentic AI Engine" cmd /k "cd /d "%~dp0Agentic AI engine" && python run_system.py"

ECHO Starting .NET Backend API...
start ".NET Backend API" cmd /k "cd /d "%~dp0fullstack\backend\MedAgent.Api\src\MedAgent.Api" && dotnet run"

ECHO Starting React Vite Frontend...
start "React Frontend" cmd /k "cd /d "%~dp0fullstack\frontend" && npm run dev"
ECHO ===================================================
ECHO All services launched successfully!
ECHO The servers are running in separate terminal windows.
pause
