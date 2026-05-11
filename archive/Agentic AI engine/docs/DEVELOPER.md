# MedAgent – Developer / AI Engineer Guide

This document is for **developers and AI engineers** who build, test, and maintain the project. For end-user run instructions, see **[README_RUN.md](README_RUN.md)**.

---

## 1. What you need (engineer setup)

| Requirement | Purpose |
|-------------|---------|
| **Python 3.9+** | Runtime |
| **OpenAI API key** | LLM and embeddings (required for full pipeline and RAG build) |
| **Git** | Version control (optional) |

No need for Redis, Docker, or MLflow to run or test locally; they are optional for production/ops.

---

## 2. One-time setup (make the project work)

Run everything from the **project root** (directory containing `config.py`, `requirements.txt`, `api/`, `agents/`, etc.).

```bash
# 1. Virtual environment (recommended)
python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Optional: dev/test dependencies (pytest for automated tests)
pip install pytest httpx

# 4. Environment: copy .env.example to .env and set OPENAI_API_KEY
# Windows: copy .env.example .env
# Mac/Linux: cp .env.example .env
# Then edit .env and set OPENAI_API_KEY=sk-your-key

# 5. Generate medical data (required for RAG; run once)
python data/generate_data.py
```

After this, the app and tests can run. **If you skip step 4**, the API will start but `/ready` will return 503 and `/consult` will fail until `OPENAI_API_KEY` is set. **If you skip step 5**, RAG has no guidelines and retrieval will return a “no data” message until you run `generate_data.py`.

---

## 3. How to run the application

**Backend (API):**
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```
- API: http://localhost:8000  
- Docs: http://localhost:8000/docs  
- Health: http://localhost:8000/health  
- Readiness: http://localhost:8000/ready  

**Frontend (UI):** In a second terminal, from project root:
```bash
streamlit run api/frontend.py --server.port 8501
```
- UI: http://localhost:8501  

Or use the scripts: `run_backend.bat` / `run_backend.sh`, then `run_frontend.bat` / `run_frontend.sh`.

---

## 4. How to test (engineer workflow)

### 4.1 Automated tests (no API key required)

From project root:

```bash
# Run all tests in evaluation/test_system.py
python evaluation/test_system.py
```

Or with pytest (if installed):

```bash
pytest evaluation/test_system.py -v
```

These tests check: config/utils/agents imports, `GET /`, `GET /health`, `GET /ready` (503 without API key is OK), and `POST /consult` validation (empty body → 422). They do **not** call the OpenAI API.

### 4.2 RAG retriever test (needs API key and data)

Builds/loads FAISS index and runs a retrieval query. Requires `OPENAI_API_KEY` (for embeddings) and `data/medical_guidelines.json` (from `python data/generate_data.py`).

```bash
python -m rag.test_rag
```

Or from project root: `python rag/test_rag.py` (ensure project root is on `PYTHONPATH` or run from root after fixing path in script; see below).

### 4.3 Full pipeline simulation (needs API key)

Runs the full agent pipeline (patient → diagnosis → scheduling → doctor) with a fixed emergency-style prompt. Requires `OPENAI_API_KEY` and `.env` loaded.

```bash
python run_simulation.py
```

### 4.4 Manual API test (backend running)

With the backend running on port 8000:

```bash
# Health
curl http://localhost:8000/health

# Consult (replace with your symptoms)
curl -X POST http://localhost:8000/consult -H "Content-Type: application/json" -d "{\"symptoms\": \"I have a headache and mild fever for 2 days.\"}"
```

---

## 5. What to change or add for the project to work

| Item | Status | Action if missing |
|------|--------|--------------------|
| **Python 3.9+** | Required | Install from python.org and use it for `pip`/`python`. |
| **requirements.txt** | Required | Run `pip install -r requirements.txt`. |
| **.env with OPENAI_API_KEY** | Required for full run | Copy `.env.example` → `.env`, set `OPENAI_API_KEY=sk-...`. |
| **data/medical_guidelines.json** | Required for RAG | Run `python data/generate_data.py` once. |
| **Prompts** | Shipped | `prompts/*.txt` must exist; paths are from `config.PROMPTS_DIR`. |
| **config.py** | Shipped | All paths default from `BASE_DIR`; no change needed unless you relocate the app. |
| **pytest** | Optional | Only for `pytest evaluation/test_system.py`. Install with `pip install pytest httpx`. |

**Nothing else is required** for a normal run and test cycle. Optional: Redis for shared rate limiting, MLflow for metrics, Docker for deployment (see [DEPLOYMENT.md](DEPLOYMENT.md)).

---

## 6. Project layout (where to change what)

| Area | Path | What to touch |
|------|------|----------------|
| Config / env | `config.py`, `.env` | Model names, limits, paths, API keys. |
| Agents | `agents/*.py` | Patient, diagnosis, scheduling, doctor logic; add nodes in `orchestrator.py`. |
| Prompts | `prompts/*.txt` | System and audit prompts; keep safety/disclaimer wording. |
| RAG | `rag/retriever.py`, `data/medical_guidelines.json` | Retrieval logic and guideline content. |
| API | `api/main.py` | Endpoints, middleware, validation. |
| Safety / rate limit | `utils/safety.py`, `utils/rate_limit.py` | Input validation, injection checks, rate limits. |
| Tests | `evaluation/test_system.py`, `rag/test_rag.py` | Add or extend tests here. |

---

## 7. Optional: Linting and formatting

No tool is mandated. If you use them:

```bash
# Example (install if you want)
pip install ruff black
ruff check .
black .
```

---

## 8. Summary checklist (engineer)

- [ ] Python 3.9+ and venv (optional but recommended)  
- [ ] `pip install -r requirements.txt`  
- [ ] `.env` with `OPENAI_API_KEY`  
- [ ] `python data/generate_data.py` run once  
- [ ] `python evaluation/test_system.py` passes  
- [ ] `uvicorn api.main:app --port 8000` and `streamlit run api/frontend.py --server.port 8501` work  
- [ ] Optional: `python run_simulation.py` and `python -m rag.test_rag` pass with API key set  

If all of the above are done, the project is set up correctly and you can run and test it as an AI engineer.
