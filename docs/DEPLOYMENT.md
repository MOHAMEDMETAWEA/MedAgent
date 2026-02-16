# MedAgent Global Deployment Guide

This document describes how to deploy the **MedAgent** system in a generic, global way—for any user, any country, and any environment (local, cloud, API, mobile backend).

## Design Principles

- **No dependency on a specific hospital, provider, or region.**  
- **Configurable** via environment variables and optional config files.  
- **Portable** across local, cloud, and containerized deployments.

---

## Prerequisites

- Python 3.9+
- OpenAI API key (for LLM and embeddings)
- (Optional) Redis for future session/memory features
- (Optional) MLflow for experiment tracking

---

## 1. Environment Configuration

Create a `.env` file in the project root (or set environment variables):

```bash
# Required
OPENAI_API_KEY=your_openai_api_key

# Optional - Model and paths
OPENAI_MODEL=gpt-4o
EMBEDDING_MODEL=text-embedding-3-small

# Optional - API URL (for frontend when backend is elsewhere)
MEDAGENT_API_URL=http://localhost:8000

# Optional - Monitoring
MLFLOW_TRACKING_URI=http://your-mlflow-server:5000
LOG_LEVEL=INFO

# Optional - Language (extensible)
DEFAULT_LANGUAGE=en
```

Paths to prompts, data, and RAG index are derived from the project layout; override via code/config if you deploy with a different structure.

---

## 2. Data and RAG Setup

Ensure medical guidelines and RAG index are available:

```bash
# Generate or ensure medical_guidelines.json exists under data/
python data/generate_data.py

# RAG index is built automatically on first run from data/medical_guidelines.json
# Index is stored under rag/faiss_index/ (configurable via config.py)
```

---

## 3. Local Run

**Backend (FastAPI):**

```bash
pip install -r requirements.txt
python api/main.py
# Or: uvicorn api.main:app --host 0.0.0.0 --port 8000
```

**Frontend (Streamlit):**

```bash
# Same machine
export MEDAGENT_API_URL=http://localhost:8000
streamlit run api/frontend.py --server.port 8501

# If backend is on another host (e.g. cloud)
export MEDAGENT_API_URL=https://your-api.example.com
streamlit run api/frontend.py --server.port 8501
```

---

## 4. Docker Deployment

From project root:

```bash
cd deployment
docker-compose up -d
```

- Backend: port 8000  
- Frontend: port 8501  
- Redis: port 6379 (optional, for future use)

Ensure `.env` is in the parent directory or passed into the containers.

---

## 5. Cloud / API Deployment

- **Backend:** Deploy `api.main:app` with any ASGI server (e.g. uvicorn, Gunicorn) behind a reverse proxy (e.g. Nginx, load balancer). Set `OPENAI_API_KEY` and any other env vars in the cloud environment.
- **Frontend:** Set `MEDAGENT_API_URL` to the public backend URL (e.g. `https://api.yourdomain.com`). Deploy Streamlit (e.g. Streamlit Cloud, or containerized) with that env var.
- **Scaling:** Run multiple backend instances behind a load balancer; each instance can use its own RAG index (e.g. shared volume or pre-built index in the image).

---

## 6. Security Checklist

- Do not commit `.env` or any file containing `OPENAI_API_KEY`.
- In production, restrict CORS `allow_origins` in `api/main.py` to your frontend origins.
- Use HTTPS for backend and frontend in production.
- Rate limiting is built-in (see below). For multi-instance deployments, set `REDIS_URL` so limits are shared.
- Keep dependencies updated (`pip install -r requirements.txt` and security audits).

### Rate limiting

- **RATE_LIMIT_ENABLED** (default: true) and **MAX_REQUESTS_PER_MINUTE** (default: 60) control in-memory rate limiting per client IP.
- Paths `/`, `/health`, `/ready`, `/docs`, `/redoc`, `/openapi.json` are exempt.
- For production with multiple API instances, set **REDIS_URL** (e.g. `redis://localhost:6379`) so rate limits are shared across instances.

### FAISS index security

- The RAG layer loads the FAISS index with `allow_dangerous_deserialization=True` (required by the library for pickle deserialization).
- **Build and store the index only in a trusted environment.** Do not load a FAISS index from untrusted sources (risk of arbitrary code execution). Generate the index from your own `data/medical_guidelines.json` (e.g. via `data/generate_data.py` and the first run of the app), or build it in CI and deploy the built index as a read-only artifact.

---

## 7. Health and Readiness

- **GET /** – Service status and version.
- **GET /health** – Lightweight liveness check (no heavy deps). Returns 200 with `status: ok` and version. Use for process/container liveness.
- **GET /ready** – Readiness probe: returns 200 when the orchestrator and RAG index are initialized and ready to serve; returns 503 otherwise. Use for load balancer readiness so traffic is sent only when the app can handle `/consult`.

Use `/health` for liveness and `/ready` for readiness in Kubernetes or similar (e.g. `livenessProbe: /health`, `readinessProbe: /ready`).

---

## 8. Risk and Disclaimer

- MedAgent is for **educational and informational use only**. It is **not** a medical device and does **not** replace professional medical advice, diagnosis, or treatment.
- Users should be directed to seek qualified healthcare and local emergency services when appropriate.
- Deployers are responsible for compliance with local regulations (e.g. data privacy, medical software) in their target regions.
