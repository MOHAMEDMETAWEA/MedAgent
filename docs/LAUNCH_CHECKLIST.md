# Pre-launch checklist

Use this list before releasing or demonstrating MedAgent.

## Automated tests
- [ ] From project root: `python evaluation/test_system.py` — all tests pass
- [ ] Optional: `pytest evaluation/test_system.py -v`

## Environment
- [ ] `.env` exists (from `.env.example`) with `OPENAI_API_KEY` set
- [ ] `python data/generate_data.py` has been run at least once (creates `data/medical_guidelines.json`)

## Run
- [ ] Backend: `uvicorn api.main:app --host 0.0.0.0 --port 8000` starts without errors
- [ ] `GET http://localhost:8000/health` returns 200
- [ ] With API key: `GET http://localhost:8000/ready` returns 200
- [ ] Frontend: `streamlit run api/frontend.py --server.port 8501` starts; UI loads at http://localhost:8501
- [ ] Full flow: submit symptoms in UI → receive summary, diagnosis, appointment, doctor review, and Generative Report (medical report, doctor summary, patient instructions)

## Optional
- [ ] `python run_simulation.py` completes (requires OPENAI_API_KEY)
- [ ] `python -m rag.test_rag` retrieves guidelines (requires OPENAI_API_KEY)

## Docs
- [ ] [README_RUN.md](README_RUN.md) — user run instructions
- [ ] [DEVELOPER.md](DEVELOPER.md) — engineer run/test
- [ ] [DEPLOYMENT.md](DEPLOYMENT.md) — deployment and security
