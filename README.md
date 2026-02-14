# 🏥 MedAgent: A Multi-Agent Smart Hospital System

> **Leveraging Generative AI, Agentic AI, and RAG for Healthcare Excellence**

---

## 📌 Overview

**MedAgent** is an intelligent healthcare management platform designed as a graduation project for the **Generative & Agentic AI** course. The system simulates a sophisticated hospital environment where autonomous AI agents collaborate in real-time to optimize clinical workflows, improve diagnostic accuracy, and enhance the overall patient experience.

By integrating **Large Language Models (LLMs)**, **Multi-Agent Systems**, and **Retrieval-Augmented Generation (RAG)**, MedAgent moves beyond simple chatbots to provide a production-grade simulation of modern, AI-integrated healthcare.

### 🌍 Global / Generic Design

MedAgent is designed to work **for any user, any country, and any healthcare environment**. It is not tied to a specific hospital, provider, database, or region. Configuration is environment-based; the frontend can point to any API URL. See **[DEPLOYMENT.md](DEPLOYMENT.md)** for deployment options and **[AUDIT_AND_IMPROVEMENTS.md](AUDIT_AND_IMPROVEMENTS.md)** for the full audit and safety improvements.

### 🏃 Quick start (run as a user)

1. **Requirements:** Python 3.9+, [OpenAI API key](https://platform.openai.com/api-keys).
2. **Setup:** From the project root folder:
   - `pip install -r requirements.txt`
   - Copy `.env.example` to `.env` and set `OPENAI_API_KEY=your_key`
   - `python data/generate_data.py` (first time only)
3. **Run:**  
   - Start the backend: `uvicorn api.main:app --host 0.0.0.0 --port 8000`  
   - In a new terminal, start the UI: `streamlit run api/frontend.py --server.port 8501`  
   - Open **<http://localhost:8501>** in your browser.

**EASIEST:** Use the unified launcher script:

- `python run_system.py`

Alternatively, use the scripts: **`run_backend.bat`** then **`run_frontend.bat`** (Windows), or **`run_backend.sh`** then **`run_frontend.sh`** (Mac/Linux).

**AI engineers / developers:** Run tests, RAG checks, and full pipeline simulation: **[DEVELOPER.md](DEVELOPER.md)**.

---

## 🏛️ DEPI Project Alignment

To ensure compliance with the **Digital Egypt Pioneers Initiative (DEPI)** graduation standards, this project explicitly maps to the official Generative AI curriculum milestones:

| DEPI Standard Milestone | MedAgent Project Milestone |
| :--- | :--- |
| **M1: Data Collection & Preprocessing** | Milestone 2: Data & RAG Pipeline Setup |
| **M2: Model Development & Training** | Milestone 3: Agent Development & M4: Report Gen |
| **M3: Advanced Techniques & Integration** | Milestone 5: Memory & Agent Coordination |
| **M4: MLOps & Model Management** | Milestone 6: Deployment & Monitoring |
| **M5: Final Report & Demonstration** | Milestone 1: Design & M7: Final Delivery |

---

## 🎯 Project Objectives

- **Autonomous Orchestration**: Implement a decentralized multi-agent system for complex medical workflows.
- **Evidence-Based Diagnosis**: Use RAG to ground AI reasoning in verified clinical protocols (WHO, NIH, CDC).
- **Proactive Monitoring**: Track patient vitals and treatment adherence through specialized agents.
- **Structured Documentation**: Automate the generation of SOAP notes and clinical reports.
- **Ethical AI**: Implement human-in-the-loop protocols and bias detection.

---

## 🤖 Multi-Agent Architecture

The system utilizes a specialized workforce of agents, coordinated via **LangGraph**:

1. **Triage Agent**: Analyzes urgency (Emergency/High/Low) and structured symptom extraction.
2. **Knowledge Agent**: Retrieves verified medical guidelines (RAG) relevant to the case.
3. **Reasoning Agent**: Performs detailed Chain-of-Thought (CoT) differential diagnosis.
4. **Validation Agent**: Cross-checks the diagnosis against retrieved evidence for consistency.
5. **Safety Agent**: Final guardrail scanning for harmful content or policy violations.
6. **Response Agent**: Generates the **Medical Report**, **Doctor Summary**, and **Patient Instructions** (in simple language). Handles bilingual support (English/Arabic).
7. **Calendar Agent**: Manages appointment scheduling and availability checks.

---

## 💡 Innovation & Added Value

> **Grading Criterion:** 10/100 Points

- **Agentic Orchestration**: Moving beyond linear chatbots to cyclic, state-aware agent workflows using **LangGraph**.
- **Clinical Reasoning**: Implementation of **Chain-of-Thought (CoT)** to provide human-readable, logical diagnostic paths.
- **Deterministic RAG**: Grounded responses that eliminate hallucinations by citing verified medical guidelines. **Generative Report Agent** uses RAG to produce medical reports, doctor summaries, and simple-language patient instructions.
- **Contextual Memory**: A hybrid memory system (Short-term Redis + Long-term ChromaDB) for seamless patient history retention.

---

## 🛠️ Technology Stack

### AI & Orchestration

- **LLMs**: OpenAI GPT-4o / GPT-4-turbo (Primary), Llama 3 (Fallback).
- **Agent Framework**: **LangGraph** (Orchestration), CrewAI (Evaluation).
- **RAG System**: LangChain / LlamaIndex with semantic search.

### Data & Memory

- **Vector Database**: **FAISS** (Local) / **Pinecone** (Production).
- **Memory**: **Redis** (Short-term context) & **ChromaDB** (Long-term patient history).
- **Embeddings**: `text-embedding-3-small`.

### Infrastructure & MLOps

- **Backend**: Python **FastAPI**.
- **Frontend**: **Streamlit** / Gradio Dashboard.
- **Monitoring**: **LangSmith** (LLM tracing), Prometheus & Grafana.
- **Version Control**: MLflow for experiment tracking and model versioning.
- **Deployment**: Docker & Docker Compose.

---

## 🚀 Key Features & Scenarios

- **Multi-Turn Symptom Intake**: Dynamic clarification questions to refine diagnostic data.
- **Chain-of-Thought Reasoning**: Transparent diagnostic steps showing *how* the AI reached a conclusion.
- **Resource Collision Handling**: Automatic rescheduling and priority-based doctor allocation.
- **Emergency Escalation**: Detection of "Red Flag" symptoms leading to immediate priority scheduling.
- **Autonomous Report Generation**: Production of structured medical documentation in standard formats (SOAP).

---

## 📊 Success Criteria & Evaluation

| Metric | Target |
| :--- | :--- |
| **Diagnosis Accuracy** | ≥ 85% compared to ground truth test cases |
| **Response Latency** | < 3 seconds for 95% of requests |
| **RAG Precision** | ≥ 0.8 for top-3 retrieval results |
| **Cost Efficiency** | < $0.50 average per patient interaction |
| **Code Coverage** | ≥ 80% unit test coverage |

---

## 📅 Project Milestones

1. **M1: Design & Ethics**: Architecture mapping and safety framework establishment.
2. **M2: Knowledge & RAG**: Building the medical knowledge base (Notebook-based preprocessing).
3. **M3: Agent Development**: Designing specialized reasoning workflows in LangGraph.
4. **M4: Generative Excellence**: Fine-tuning prompts and structured SOAP report templates.
5. **M5: Memory & Coordination**: Implementing long-term history and complex patient simulations.
6. **M6: Deployment & MLOps**: FastAPI, MLflow tracking, Docker, and monitoring dashboards.
7. **M7: Final Presentation**: Performance benchmarking and live demonstration.

---

## 👥 Task Division & Team Roles

> **Grading Criterion:** 5/100 Points

- **AI Reasoning Engineer**: Responsible for agent logic, prompt engineering (CoT), and report generation.
- **Data & RAG Architect**: Responsible for the vector database, medical knowledge base, and embedding pipelines.
- **System Integrator**: Responsible for FastAPI development, Redis memory management, and agent state persistence.
- **MLOps & DevOps Lead**: Responsible for Docker containerization, MLflow tracking, and monitoring dashboards.
- **Quality & Documentation Lead**: Responsible for the ethical framework, technical reports, and final presentation.

---

## 📂 Project Structure

```text
medagent-smart-hospital/
│
├── agents/             # Agent logic (LangGraph workflows)
├── rag/                # Knowledge base, embeddings, and retrievers
├── memory/             # Persistent state and patient history
├── api/                # FastAPI endpoints & authentication
├── prompts/            # Sophisticated prompt library & templates
├── data/               # Synthetic patient data & medical guidelines
├── deployment/         # Docker, CI/CD, and MLOps config
├── notebooks/          # R&D and performance experiments
└── evaluation/         # RAG metrics and agent behavior logs
```

---

## ⚠️ Ethical Considerations & Safety

- **Human-in-the-Loop**: All AI-generated diagnoses require validation by the "Doctor Agent" (simulating a clinician).
- **Transparency**: Every recommendation cites its source from the medical knowledge base.
- **Disclaimer**: This system is for **educational simulation only** and is not a medical device.
- **Bias Mitigation**: Active monitoring for gender or socioeconomic bias in treatment recommendations.

---

## 👨‍💻 Author

**Mohamed Mostafa Metawea**  
*Graduation Project - Generative & Agentic AI Track*

---

## 📜 License

This project is for educational and research purposes only.

---
> 💡 *MedAgent demonstrates the future of "Autonomous Healthcare" where AI serves as a tireless collaborator for medical professionals.*
