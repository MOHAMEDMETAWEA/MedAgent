"""
Safe Run Script for MedAgent.
Ensures environment is set up and starts API + Frontend.
"""
import os
import subprocess
import sys
import threading
import time
import requests

def run_backend():
    print("[Launcher] Starting Backend API on port 8000...")
    subprocess.run([sys.executable, "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"])

def run_frontend():
    # Wait for backend
    time.sleep(5)
    print("[Launcher] Starting Frontend UI...")
    subprocess.run([sys.executable, "-m", "streamlit", "run", "api/frontend.py"])

def check_env():
    print("[Launcher] Checking Environment...")
    if not os.path.exists(".env"):
        print("[WARNING] .env file not found! System may fail authorization.")
        # Proceed anyway as config.py has defaults/errors
    else:
        print("[Launcher] .env found.")

if __name__ == "__main__":
    check_env()
    
    # Run in parallel threads
    backend_thread = threading.Thread(target=run_backend)
    backend_thread.start()
    
    try:
        run_frontend()
    except KeyboardInterrupt:
        print("[Launcher] Stopping...")
        # Threads are daemon=False by default, so we might need to kill manually
        sys.exit(0)
