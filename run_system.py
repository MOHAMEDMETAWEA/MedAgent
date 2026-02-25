"""
Unified Startup Script for MEDAgent.
Launches the FastAPI backend and Streamlit frontend in parallel.
"""
import subprocess
import sys
import time
import os

def pre_flight_checks():
    """Ensure system requirements are met before launch."""
    print("[SYSTEM] Running Pre-flight Checks...")
    
    # 1. Check .env
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path):
        print("[WARNING] .env file missing! Defaulting to environment variables.")
    else:
        from dotenv import load_dotenv
        load_dotenv()

    # 2. Check OpenAI Key
    key = os.getenv("OPENAI_API_KEY")
    if not key or "your-openai-key" in key:
        print("[CRITICAL] OPENAI_API_KEY is not set correctly in .env. LLM features will fail.")
        return False

    # 3. Check RAG Index
    index_path = os.path.join(os.path.dirname(__file__), "rag", "faiss_index", "index.faiss")
    if not os.path.exists(index_path):
        print("[INFO] FAISS index missing. Initializing Knowledge Base...")
        try:
            # We run this in-process or as sub-task
            from rag.retriever import MedicalRetriever
            # This triggers initialization
            MedicalRetriever()
            print("[OK] Knowledge Base Initialized.")
        except Exception as e:
            print(f"[ERROR] Failed to initialize RAG: {e}")
            # Non-critical for launch, but warns
    
    # 4. Check Encryption Key
    enc_key = os.getenv("DATA_ENCRYPTION_KEY")
    if not enc_key:
        print("[CRITICAL] DATA_ENCRYPTION_KEY is missing. Security layer cannot start.")
        return False
    
    # 5. Check JWT Secret
    jwt_key = os.getenv("JWT_SECRET_KEY")
    if not jwt_key:
        print("[CRITICAL] JWT_SECRET_KEY is missing. Authentication cannot start.")
        return False
        
    print("[OK] Pre-flight checks passed.\n")
    return True

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
        if not pre_flight_checks():
            print("[CRITICAL] Pre-flight checks failed. Aborting startup.")
            sys.exit(1)
            
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
