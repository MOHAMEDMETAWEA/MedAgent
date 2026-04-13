# MedAgent Ecosystem

MedAgent is a comprehensive medical AI ecosystem consisting of three closely integrated microservices. This document serves as the root index for developers to understand the architecture and quickly spin up the environment.

## 🏗️ Architecture Stack

MedAgent is divided into two primary workspaces:

1. **`Agentic AI engine/`** (Python/FastAPI) 🔥
   - **Role:** Handles core medical intelligence, multi-agent LangGraph orchestration, vision analysis, and Tree-of-Thought clinical reasoning.
   - **Port:** `8000` (API), `8501` (Dashboard)
   - **Docs:** Read `Agentic AI engine/README.md` for deep dive.
   
2. **`fullstack/backend/`** (.NET 8 C# API) ⚙️
   - **Role:** Core business logic, User authentication (JWT), Medical ID storage, and Photo metadata management using strict Clean Architecture.
   - **Port:** `10000`
   
3. **`fullstack/frontend/`** (React 19 + Vite) 🎨
   - **Role:** The beautifully-designed glassmorphic user interface. Routes between the C# backend for user data and the Python engine for AI consultations.
   - **Port:** `5173`
   - **Docs:** Read `fullstack/PROJECT_OVERVIEW.md`.

---

## 🚀 Quick Start Guide

To run the entire MedAgent platform locally, you will need to start all three services.

### 1. Start the .NET Backend
This handles your database and standard user authentication.
```bash
cd fullstack/backend/MedAgent.Api
dotnet run --project src/MedAgent.Api
```

### 2. Start the Agentic AI Engine
This handles all the LangGraph LLM orchestration and image processing.
```bash
cd "Agentic AI engine"
# Ensure your virtual environment is active
python run_server.py
```

### 3. Start the React Frontend
This is what the user interacts with.
```bash
cd fullstack/frontend
npm install
npm run dev
```

## 🔐 Environment Variables

Make sure the `.env` files are configured in their respective directories:
- `Agentic AI engine/.env` needs your `OPENAI_API_KEY` and `JWT_SECRET_KEY`.
- `fullstack/frontend/.env` needs `VITE_API_BASE_URL=http://localhost:10000` and `VITE_AI_ENGINE_BASE_URL=http://localhost:8000`.

## 🤖 Connectivity Note
The React Frontend communicates with BOTH backends:
- `src/services/apiClient.js` routes to the .NET Backend.
- `src/services/api/aiService.js` routes to the Python Agentic AI Engine.
