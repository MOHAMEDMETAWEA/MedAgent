# MedAgent 🩺

> An AI-powered medical ecosystem designed to provide intelligent triage, healthcare solutions, and multi-turn clinical conversations.

[![Status](https://img.shields.io/badge/status-active-success)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()

## 📖 Project Overview

MedAgent is a production-grade AI medical triage assistant. It is built to conduct multi-turn medical conversations (in English and Arabic), provide triage assessments grounded in retrieved medical guidelines, generate doctor handoff summaries, and detect red-flag symptoms for immediate emergency escalation. The system also supports preliminary medical image analysis (such as X-rays and skin lesions).

This repository is organized into two distinct environments, covering different architectural approaches to building the MedAgent platform:

1. **`MedAgent-main/`**: A full-stack reference implementation utilizing a unified Next.js + FastAPI stack.
2. **`archive/`**: A custom microservices architecture utilizing .NET, React, and Python (LangGraph).

---

## 🌟 Key Features

- **Bilingual Conversations:** Seamlessly converses in Arabic and English, including code-switching.
- **Intelligent Triage:** Evaluates symptoms and categorizes cases (emergency, urgent, routine) based on medical guidelines.
- **Doctor Handoff:** Generates comprehensive summaries for patients to share with clinicians.
- **Emergency Escalation:** Detects red flags and recommends immediate medical attention when necessary.
- **Medical Vision:** Analyzes medical images (X-rays, skin lesions, etc.) to provide preliminary insights.
- **Interoperability:** Exports handoff summaries in FHIR R4 and HL7 v2 formats for EHR integration.

---

## 🚀 How to Use and Run the Project

Depending on the architecture you wish to run, follow the respective guide below.

### Option A: The Reference Implementation (Next.js + FastAPI)
This is the recommended, full-stack implementation serving as a robust reference, built with Next.js 16 (App Router), FastAPI, PostgreSQL + pgvector, and Qwen2.5.

**Prerequisites:**
- Python **3.11+** (managed via `uv`)
- Node.js **20+** and **pnpm 9+**
- Docker & Docker Compose
- PostgreSQL **16+** with pgvector (provided via docker-compose)

**Setup Instructions:**
1. Navigate to the `MedAgent-main` directory:
   ```bash
   cd MedAgent-main
   ```
2. Set up the environment variables:
   ```bash
   cp backend/.env.example backend/.env
   ```
   *(Make sure to edit `backend/.env` and fill in required values like your `LLM_API_KEY`)*
3. Start the infrastructure (PostgreSQL, Redis, Mailpit, Backend, and Frontend):
   ```bash
   make up
   ```
4. Seed the medical knowledge base (Required for RAG features):
   ```bash
   make seed-kb
   ```

**Accessing the Services:**
- **Frontend App:** [http://localhost:3000](http://localhost:3000)
- **Backend API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Mailpit (Dev SMTP):** [http://localhost:8025](http://localhost:8025)

---

### Option B: The Custom Microservices Architecture (.NET + React + Python)
This environment uses a rigorous microservices approach with a focus on strict Clean Architecture and LangGraph orchestration.

**Prerequisites:**
- .NET 8 SDK
- Python 3.10+
- Node.js & npm

**Setup Instructions:**

**1. Start the .NET Backend** (Handles database and user authentication)
```bash
cd archive/fullstack/backend/MedAgent.Api
dotnet run --project src/MedAgent.Api
```
*(Runs on port 10000)*

**2. Start the Agentic AI Engine** (Handles LangGraph LLM orchestration and image processing)
```bash
cd "archive/Agentic AI engine"
# Create and activate your python virtual environment
python -m venv venv
# Windows: venv\Scripts\activate | Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
python run_server.py
```
*(Ensure `archive/Agentic AI engine/.env` is configured with `OPENAI_API_KEY` and `JWT_SECRET_KEY`. Runs on port 8000)*

**3. Start the React Frontend** (The user interface)
```bash
cd archive/fullstack/frontend
npm install
npm run dev
```
*(Ensure `archive/fullstack/frontend/.env` is configured with `VITE_API_BASE_URL=http://localhost:10000` and `VITE_AI_ENGINE_BASE_URL=http://localhost:8000`. Runs on port 5173)*

---

## ⚠️ Medical Disclaimer
**MedAgent is an informational tool and AI assistant, not a substitute for professional medical advice, diagnosis, or treatment. Always consult a licensed physician.**

## 📄 License
This project is licensed under the MIT License.
