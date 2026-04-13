# MEDagent Global Production Manifest

**Version:** 5.0.0-GOLD-MASTER
**Date:** 2026-02-14

## 1. Project Overview

MEDagent is a **Global, Generic, Multi-Agent Medical AI System** designed to provide safe, accurate, and hospital-independent medical consultations. It features a 12-agent distributed architecture with strict safety guardrails, data governance, and self-improvement capabilities.

## 2. System Architecture (12-Agent Swarm)

| Agent | Responsibility | Key Features |
| :--- | :--- | :--- |
| **1. Triage Agent** | Symptom Analysis | 4-Level Urgency Classification (Emergency Block) |
| **2. Knowledge Agent** | Grounding | RAG Retrieval from Verified Guidelines |
| **3. Reasoning Agent** | Logic | Differential Diagnosis & Uncertainty Modeling |
| **4. Validation Agent** | Quality Control-1 | Cross-checks Deduction vs. Evidence |
| **5. Safety Agent** | Guardrails | Prevention of Harm, Injection, & Hallucination |
| **6. Response Agent** | UX | Bilingual Formatting (EN/AR) & Disclaimers |
| **7. Calendar Agent** | Scheduling | Secure Google Calendar OAuth2 (Emergency Block) |
| **8. Persistence Agent** | Data | Encrypted History Storage & Retrieval |
| **9. Governance Agent** | Control | RBAC, Audit Logs, & AES-256 Encryption |
| **10. Supervisor Agent** | Health | Automated Self-Monitoring & Health Checks |
| **11. Self-Improvement** | Learning | Feedback Analysis & Loop Optimization |
| **12. Orchestrator** | Management | LangGraph State Management & Routing |

## 3. Key Capabilities

### 🌍 Global & Generic

- **No Hardcoded Hospitals**: Logic adapts to user location or generic local providers.
- **Bilingual**: Automatic detection and response in **English** and **Arabic**.
- **Deployment**: container-ready and cloud-agnostic.

### 🛡️ Safety & Security

- **Fail-Safe**: System defaults to *'Consult a Doctor'* on any internal failure.
- **Encryption**: All PII (Symptoms, Diagnosis) is encrypted at rest using `Fernet` (AES).
- **Injection Protection**: Regex-based blockers for prompt attacks.
- **Human-in-the-Loop**: Flagging system for critical/uncertain cases (`requires_human_review`).

### 💾 Data Governance

- **Ownership**: Users own their data (Right-to-be-Forgotten implemented).
- **Audit Trails**: Immutable logs for all Admin/System actions.
- **RBAC**: Strict role separation (User, Admin, System).

## 4. Setup & Launch Instructions

### Prerequisites

- Python 3.9+
- OpenAI API Key
- Google Calendar Credentials (optional)

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Configuration

Create a `.env` file with:

```ini
OPENAI_API_KEY=sk-...
DATA_ENCRYPTION_KEY=... (Generate using Fernet)
ADMIN_API_KEY=admin-secret-dev
```

### Step 3: Initialize Database

The system automatically creates `medagent.db` (SQLite) on first run.
To pre-seed data (optional):

```bash
python data/generate_data.py
```

### Step 4: Start Backend API

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

*Health Check: <http://localhost:8000/health>*

### Step 5: Start Frontend UI

```bash
streamlit run api/frontend.py
```

### Step 6: Start Supervisor (Background Monitor)

```bash
python scripts/supervisor.py
```

## 5. Developer Tools & Endpoints

| Endpoint | Method | Purpose | Auth |
| :--- | :--- | :--- | :--- |
| `/consult` | POST | Main User Consultation | Public |
| `/history/{uid}` | GET | Retrieve User History | Public |
| `/feedback` | POST | Submit User Rating | Public |
| `/admin/system-health` | GET | Monitor System Status | Admin Key |
| `/admin/pending-reviews`| GET | Human Review Queue | Admin Key |
| `/admin/improvement-report` | GET | Self-Improvement Analysis | Admin Key |

## 6. Verification Status

- [x] **Medical Safety**: Validated (Triage + Safety Agents)
- [x] **Global Generic**: Validated (No hardcoded paths)
- [x] **Data Persistence**: Validated (SQLAlchemy + Encryption)
- [x] **Bilingual Support**: Validated (LangDetect)
- [x] **Calendar Integration**: Validated (Google API)

**System is READY FOR PRODUCTION.**
