#!/usr/bin/env bash
# Run MedAgent web UI. Start the backend first (run_backend.sh).
cd "$(dirname "$0")"
[[ -f venv/bin/activate ]] && source venv/bin/activate
echo "Starting MedAgent UI at http://localhost:8501 ..."
streamlit run api/frontend.py --server.port 8501
