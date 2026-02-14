#!/usr/bin/env bash
# Run MedAgent backend API. Use from project root.
cd "$(dirname "$0")"
[[ -f venv/bin/activate ]] && source venv/bin/activate
echo "Starting MedAgent API at http://localhost:8000 ..."
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
