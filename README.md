# MedAgent 🩺

> An AI-powered medical ecosystem designed to provide intelligent triage, healthcare solutions, and multi-turn clinical conversations.

[![Status](https://img.shields.io/badge/status-active-success)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()

## 📖 Comprehensive Project Overview

MedAgent is a production-grade AI medical triage assistant. It is built to conduct multi-turn medical conversations (in English and Arabic), provide triage assessments grounded in retrieved medical guidelines, generate doctor handoff summaries, and detect red-flag symptoms for immediate emergency escalation. The system also supports preliminary medical image analysis (such as X-rays and skin lesions).

This repository is organized into two distinct environments, covering different architectural approaches to building the MedAgent platform:

1. **`MedAgent-main/`**: A full-stack reference implementation utilizing a unified Next.js + FastAPI stack.
2. **`archive/`**: A custom microservices architecture utilizing .NET, React, and Python (LangGraph).

This documentation serves as the master guide to understanding, deploying, and working with both implementations of the MedAgent ecosystem.

---

## 🌟 Core Capabilities & Features

Regardless of the underlying architecture, MedAgent is designed to deliver the following core features:

- **Bilingual Conversations:** Seamlessly converses in Arabic and English, including code-switching based on patient preference.
- **Intelligent Triage Engine:** Evaluates user symptoms and categorizes cases into Emergency, Urgent, or Routine based on established medical guidelines.
- **Doctor Handoff:** Generates comprehensive clinical summaries (SOAP notes) for patients to share with clinicians.
- **Emergency Escalation (Red Flags):** Built-in safety mechanisms detect critical "red-flag" symptoms and recommend immediate medical attention or emergency services.
- **Medical Vision (Image Analysis):** Analyzes medical images (X-rays, skin lesions, etc.) utilizing vision models to provide preliminary insights.
- **EHR Interoperability:** Exports handoff summaries in FHIR R4 and HL7 v2 formats for seamless Electronic Health Record integration.
- **Knowledge-Grounded Reasoning (RAG):** Answers are grounded in a trusted medical knowledge base to prevent hallucination.

---

## 🏗️ 1. The Reference Implementation (`MedAgent-main/`)

This is the recommended, full-stack implementation serving as a robust reference, built with Next.js 16 (App Router), FastAPI, PostgreSQL + pgvector, and Qwen2.5. It focuses on a clean two-tier architecture.

### Tech Stack
- **Backend:** FastAPI, SQLAlchemy 2 (async), PostgreSQL + pgvector, Redis, Alembic
- **Frontend:** Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4, shadcn/ui
- **AI/ML Engine:** Qwen2.5 (via OpenRouter), multilingual-e5 embeddings, bge-reranker-v2-m3, ReAct Agent framework
- **Infrastructure:** Docker, GitHub Actions, Prometheus, OpenTelemetry

### Project Structure (`MedAgent-main/`)
- `backend/` - FastAPI app, AI agent, RAG, domain modules
- `frontend/` - Next.js 16 app (App Router, i18n, RTL)
- `notebooks/` - ML experiments (data, fine-tuning, eval)
- `scripts/` - Knowledge base seeding, ops, audit verification
- `data/` - Datasets & knowledge base
- `docs/` - Architecture, API, deployment guides

### Running the Reference Implementation

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
   *(Ensure you fill in required values like `LLM_API_KEY` in `backend/.env`)*
3. Start the core infrastructure (PostgreSQL, Redis, Mailpit, Backend, and Frontend):
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

## 🏗️ 2. The Microservices Architecture (`archive/`)

This environment uses a rigorous microservices approach with a focus on strict Clean Architecture and LangGraph orchestration. It separates the business logic, user interface, and AI reasoning into three distinct applications.

### Tech Stack & Architecture
1. **Agentic AI Engine (`Agentic AI engine/`)** - Python/FastAPI
   - Handles core medical intelligence, multi-agent LangGraph orchestration, vision analysis, and Tree-of-Thought clinical reasoning.
   - Runs on Port **8000**.
2. **C# .NET Backend (`fullstack/backend/`)** - .NET 8
   - Manages core business logic, user authentication (JWT), Medical ID storage, and Photo metadata management using strict Clean Architecture.
   - Runs on Port **10000**.
3. **React Frontend (`fullstack/frontend/`)** - React 19 + Vite
   - A beautifully-designed glassmorphic user interface. Routes between the C# backend for user data and the Python engine for AI consultations.
   - Runs on Port **5173**.

### Running the Microservices Architecture

**Prerequisites:**
- .NET 8 SDK
- Python 3.10+
- Node.js & npm

**Setup Instructions:**

1. **Start the .NET Backend** (Database and User Auth)
   ```bash
   cd archive/fullstack/backend/MedAgent.Api
   dotnet run --project src/MedAgent.Api
   ```

2. **Start the Agentic AI Engine** (LangGraph LLM Orchestration)
   ```bash
   cd "archive/Agentic AI engine"
   # Create and activate your python virtual environment
   python -m venv venv
   # Windows: venv\Scripts\activate | Mac/Linux: source venv/bin/activate
   pip install -r requirements.txt
   python run_server.py
   ```
   *Note: Ensure `archive/Agentic AI engine/.env` is configured with `OPENAI_API_KEY` and `JWT_SECRET_KEY`.*

3. **Start the React Frontend** (User Interface)
   ```bash
   cd archive/fullstack/frontend
   npm install
   npm run dev
   ```
   *Note: Ensure `archive/fullstack/frontend/.env` is configured with `VITE_API_BASE_URL=http://localhost:10000` and `VITE_AI_ENGINE_BASE_URL=http://localhost:8000`.*

---

## 🛡️ Safety & Reliability

Patient safety is the primary directive of MedAgent. The AI pipeline integrates multiple safety stages:
- **Hallucination Detection:** An autonomous guardrail agent verifies all medical output against established knowledge bases.
- **PHI Protection:** Patient Health Information (PHI) is scrubbed or encrypted before transit to any external LLMs.
- **Deterministic Triage Limits:** Emergency evaluations enforce immediate circuit breakers, stopping standard dialogue to prioritize human escalation.

## ⚠️ Medical Disclaimer
**MedAgent is an informational tool and AI assistant, not a substitute for professional medical advice, diagnosis, or treatment. Always consult a licensed physician or call emergency services if you suspect a medical emergency.**

## 📄 License
This project is licensed under the MIT License. See the `LICENSE` file for details.
