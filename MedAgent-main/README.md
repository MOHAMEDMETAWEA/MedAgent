# MedAgent 🩺

> Bilingual (Arabic + English) medical triage AI assistant — grounded, safe, and built for Arabic-speaking patients.

[![Status](https://img.shields.io/badge/status-in%20development-yellow)]()
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue)]()
[![Next.js](https://img.shields.io/badge/Next.js-16-black)]()

## Overview

MedAgent is a production-grade AI medical triage assistant that:

- Conducts multi-turn medical conversations in **Arabic and English** (including code-switching)
- Provides **triage assessment** (emergency / urgent / routine) grounded in retrieved medical guidelines
- Generates a **doctor handoff summary** patients can share with clinicians
- Detects **red-flag symptoms** and escalates emergencies immediately
- Supports **preliminary medical image analysis** (X-ray, skin lesions, etc.)
- Exports handoffs as **FHIR R4** and **HL7 v2** for EHR interoperability

⚠️ **Medical Disclaimer:** MedAgent is an informational tool, not a substitute for professional medical advice, diagnosis, or treatment. Always consult a licensed physician.

## Tech Stack

**Backend:** FastAPI · SQLAlchemy 2 (async) · PostgreSQL + pgvector · Redis · Alembic
**Frontend:** Next.js 16 (App Router) · React 19 · TypeScript · Tailwind v4 · shadcn/ui
**AI/ML:** Qwen2.5 (via OpenRouter) · multilingual-e5 embeddings · bge-reranker-v2-m3 · ReAct Agent
**Infra:** Docker · GitHub Actions · Prometheus · OpenTelemetry

## Prerequisites

- Python **3.11+** (managed via [`uv`](https://github.com/astral-sh/uv))
- Node.js **20+** and **pnpm 9+**
- Docker & Docker Compose
- PostgreSQL **16+** with pgvector (provided via docker-compose)

## Quick Start

```bash
git clone https://github.com/hossam7asan/medagent.git
cd medagent
cp backend/.env.example backend/.env       # fill in required values (LLM_API_KEY, etc.)
make up                                     # starts postgres, redis, mailpit, backend, frontend
make seed-kb                                # seed the medical knowledge base (required!)
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API docs | http://localhost:8000/docs |
| Mailpit (dev SMTP) | http://localhost:8025 |

## Project Structure

```
medagent/
├── backend/           # FastAPI app, AI agent, RAG, domain modules
├── frontend/          # Next.js 16 app (App Router, i18n, RTL)
├── notebooks/         # ML experiments (data, fine-tuning, eval)
├── scripts/           # Knowledge base seeding, ops, audit verification
├── data/              # Datasets & knowledge base (gitignored)
├── docs/              # Architecture, API, deployment guides
└── plan.md            # Master project plan & specification
```

## Documentation

- 📋 [Master Plan](plan.md) — complete project specification
- 🏛️ [Architecture](docs/architecture.md) — system design & data flow
- 🔌 [API Reference](docs/api-reference.md) — endpoint schemas & examples
- 🚀 [Deployment](docs/deployment.md) — Docker, CI/CD, production checklist
- 🤖 [AI Pipeline](docs/ai-pipeline.md) — agent design, RAG, safety stages
- 🛡️ [Safety Model](docs/safety.md) — red flags, hallucination detection, triage
- 🧑‍💻 [Developer Guide](docs/development.md) — local setup, testing, conventions

## Status

✅ Phase 1: Foundation — Auth, DB, Docker, CI/CD
✅ Phase 2: AI Core — ReAct agent, 13 clinical tools, streaming chat
✅ Phase 2.5: Safety & Polish — Hallucination gate, PHI encryption, glassmorphic UI
🔄 Phase 3: ML Pipeline — Data collection, LoRA fine-tuning, evaluation *(in progress)*
🔄 Phase 4: Deploy & Docs — Production release, final documentation *(in progress)*

See [docs/tasks/STATUS.md](docs/tasks/STATUS.md) for detailed task tracker.

## License

MIT © 2026 Hossam Hassan

