#!/bin/bash
echo "=========================================================="
echo "      MEDAGENT GLOBAL SYSTEM - PRODUCTION STARTUP"
echo "=========================================================="
echo ""
echo "[1/3] Checking Environment..."
if [ ! -f .env ]; then
    echo "[WARNING] .env file not found. Copying form example..."
    cp .env.example .env
    echo "Please edit .env with your API keys!"
    read -p "Press Enter to continue..."
fi

echo "[2/3] Checking Dependencies..."
if pip install -r requirements.txt > /dev/null 2>&1; then
    echo "[OK] Dependencies ready."
else
    echo "[ERROR] Failed to install requirements."
    exit 1
fi

echo "[3/3] Launching System..."
echo ""
echo "* Backend API: http://localhost:8000"
echo "* Frontend UI: http://localhost:8501"
echo ""

python3 run_system.py
