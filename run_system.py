"""
Unified Startup Script for MEDAgent.
Launches the FastAPI backend and Streamlit frontend in parallel.
"""
import subprocess
import sys
import time
import os

def run_backend():
    print("[SYSTEM] Starting Backend API (Uvicorn)...")
    # Using sys.executable to ensure we use the same python environment
    return subprocess.Popen([sys.executable, "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"])

def run_frontend():
    print("[SYSTEM] Starting Frontend UI (Streamlit)...")
    # Streamlit usually needs special handling to run via python -m
    return subprocess.Popen([sys.executable, "-m", "streamlit", "run", "api/frontend.py", "--server.port", "8501"])

if __name__ == "__main__":
    print("="*60)
    print("      MEDAGENT GLOBAL SYSTEM - STARTUP INITIATED")
    print("="*60)
    
    backend_proc = None
    frontend_proc = None
    
    try:
        backend_proc = run_backend()
        time.sleep(3) # Give backend a moment to bind to port
        
        frontend_proc = run_frontend()
        
        print("\n[SUCCESS] Both services are running.")
        print("Backend: http://localhost:8000")
        print("Frontend: http://localhost:8501")
        print("\nPress Ctrl+C to terminate both servers.")
        
        # Keep the main script alive while processes are running
        while True:
            if backend_proc.poll() is not None:
                print("[ERROR] Backend process terminated unexpectedly.")
                break
            if frontend_proc.poll() is not None:
                print("[ERROR] Frontend process terminated unexpectedly.")
                break
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n[SYSTEM] Shutting down...")
    finally:
        if backend_proc:
            backend_proc.terminate()
        if frontend_proc:
            frontend_proc.terminate()
        print("[SYSTEM] All services stopped.")
