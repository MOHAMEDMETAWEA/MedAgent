# 🏥 MEDagent Global System - Final Production Build

**Version:** 5.3.0-PRODUCTION
**Status:** Hardened Build with Observability & Lineage
**Architecture:** Multi-Agent Swarm (Specialized Agents)

## 🚀 Quick Start (Production)

This is the designated entry point for the full MEDagent system.

### 1. Setup Environment

Ensure Python 3.9+ is installed.

```bash
pip install -r requirements.txt
cp .env.example .env
# Set in .env:
# OPENAI_API_KEY, DATA_ENCRYPTION_KEY, JWT_SECRET_KEY, ADMIN_API_KEY, AUDIT_SIGNING_KEY
```

### 2. Initialize System

```bash
python data/generate_data.py
```

### 3. Launch System (API + Frontend + Supervisor)

We have provided a unified launcher script:

```bash
python run_system.py
```

- **Frontend UI:** <http://localhost:8501>
- **Backend API:** <http://localhost:8000/docs>
- **Metrics:** <http://localhost:8000/metrics>
- **Health:** /health/live, /health/ready

---

## 📂 Project Structure

- **`agents/`**: Core intelligence (Triage, Reasoning, Safety, Calendar, etc.)
- **`api/`**: FastAPI backend and Streamlit frontend.
- **`data/`**: Medical guidelines and vector store generation.
- **`database/`**: SQLAlchemy models for persistence and governance.
- **`scripts/`**: Supervisor and reporting tools.
- **`tests/`**: Automated test suite.

## 🛡️ Key Features

- **Global & Generic**: Works for any user, anywhere. No specific hospital dependency.
- **Bilingual**: Supports **English** and **Arabic** natively.
- **Safe**: Full RAG grounding + Safety Agent guardrails.
- **Secure**: AES-256 Encryption for patient data + RBAC for admins.
- **Observability**: Prometheus metrics & minimal OpenTelemetry spans.
- **Self-Improving**: Feedback loop implementation.

## 📄 Documentation

- **[FINAL_PROJECT_MANIFEST.md](./FINAL_PROJECT_MANIFEST.md)**: Detailed architecture and deployment guide.
- **[AUDIT_COMPLIANCE_REPORT.md](./AUDIT_COMPLIANCE_REPORT.md)**: Safety and compliance verification.

## 🔌 Interoperability & Admin

- API: `POST /interop/fhir`, `POST /interop/hl7` (report exports)
- Admin: `POST /admin/audit-export` (signed evidence), `POST /experiments/ab-test`, `POST /registry/review`
- Header required for admin: `X-Admin-Key: ${ADMIN_API_KEY}`

---
*Built with LangChain, LangGraph, FastAPI, and Streamlit.*
