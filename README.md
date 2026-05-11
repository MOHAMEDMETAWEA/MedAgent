# MedAgent 🩺

Welcome to the **MedAgent** repository. This repository houses the codebase and reference implementations for MedAgent, an AI-powered medical ecosystem designed to provide intelligent triage and healthcare solutions. 

This repository is organized into distinct environments, covering different architectural approaches to building the MedAgent platform.

## 📂 Repository Structure

### 1. `archive/` - Custom Microservices Architecture
The `archive/` directory contains a comprehensive microservices-based approach with a focus on strict Clean Architecture and LangGraph orchestration.
- **Frontend:** React 19 + Vite (Beautiful glassmorphic UI)
- **Backend:** .NET 8 C# API (User auth, business logic, medical ID storage)
- **Agentic AI Engine:** Python / FastAPI (LangGraph orchestration, multi-agent medical intelligence, vision analysis)
- *See the [`archive/README.md`](archive/README.md) for detailed startup instructions.*

### 2. `MedAgent-main/` - Reference Implementation
A full-stack implementation serving as a robust reference, built for Arabic-speaking patients and utilizing advanced LLM features.
- **Frontend:** Next.js 16 (App Router), Tailwind v4
- **Backend:** FastAPI, SQLAlchemy 2 (async), PostgreSQL + pgvector
- **AI/ML:** Qwen2.5 (OpenRouter), ReAct Agent, RAG capabilities
- *See the [`MedAgent-main/README.md`](MedAgent-main/README.md) for setup and deployment guides.*

## 🚀 Getting Started

Depending on the architecture you wish to run or explore, navigate to the respective directory and follow its README instructions.

- For the **Microservices (.NET + React + Python)** approach, go to:
  ```bash
  cd archive
  ```
  Then follow the guide to start the C# API, React Frontend, and Python Engine.

- For the **Next.js + FastAPI** approach, go to:
  ```bash
  cd MedAgent-main
  ```
  Then follow the Docker Compose instructions to spin up the infrastructure.

## ⚠️ Medical Disclaimer
MedAgent is an informational tool and AI assistant, not a substitute for professional medical advice, diagnosis, or treatment. Always consult a licensed physician.
