# 🏥 MedAgent: The Global Autonomous Clinical Orchestrator

> **A State-of-the-Art Multi-Agent Smart Hospital System Powered by Generative & Agentic AI**

**Version:** v5.3.0-PRODUCTION (Hardened)  
**Project Track:** DEPI Graduation Project - Generative & Agentic AI  
**Author:** Mohamed Mostafa Metawea  
**Validation Status:** READY FOR DEPLOYMENT (Full-Stack Audit Passed)

---

## 📌 1. Project Overview & Vision

**MedAgent** is a hyper-connected, autonomous medical decision-support ecosystem. It is designed to simulate a production-grade digital hospital where **12+ specialized AI agents** collaborate using **LangGraph** orchestration.

The system moves beyond simple chatbots into a **Stateful Agentic Workforce** that manages:

- **Autonomous Patient Triage** & Risk Stratification.
- **Multimodal Visual Diagnostics** (X-ray, CT, MRI, DICOM).
- **Tree-of-Thought (ToT) Reasoning** for complex differential diagnosis.
- **Audit-Chain Persistence**: A cryptographically linked ledger of medical events.
- **Generative Care Planning**: AI-powered personalized wellness and education hubs.
- **Healthcare Interoperability**: Native FHIR Bundle and HL7 v2 generation.

---

## 🤖 2. The Agentic Workforce

MedAgent operates through a specialized hierarchy of agents, each with a deterministic role and governed by a central **Prompt Registry**:

### 🧠 Clinical Intelligence

* **Triage Agent**: Implements ESI (Emergency Severity Index) to prioritize cases.
- **Knowledge Agent**: RAG specialist querying NIH/WHO guidelines for evidence-based grounding.
- **Reasoning Agent**: Powerhouse performing **Tree-of-Thought (ToT)** multi-branch analysis.
- **Vision Agent**: High-fidelity multimodal analyzer (GPT-4o Vision) for clinical scans and photos.
- **Second Opinion Agent**: Adversarial specialist that cross-checks primary reasoning.
- **Generative Engine Agent**: Creates personalized care plans, educational summaries, and simulations.

### 🛡️ Governance & Safety

* **Safety Agent**: Real-time screening for PII, clinical errors, and unsafe medical advice.
- **Governance Agent**: Central authority for **AES-256 encryption** and RBAC.
- **Verification Agent**: Validates physician credentials for clinical "Doctor Mode".
- **Human Review Agent**: Manages the Clinician-in-the-Loop audit trail for high-risk flags.

### ⚙️ Operational Layer

* **Persistence Agent**: Orchestrates the **Audit-Chain Memory Graph** (WORM-compatible).
- **Report Agent**: Generates SOAP-standard reports in PDF, PNG, and Text formats.
- **Medication Agent**: Tracks dosages, frequencies, and digital health reminders.
- **Authentication Agent**: Secure JWT-based identity and session management.

---

## 🔬 3. Technical Core & Hardening

### **Audit Hash Chaining (Medical Integrity)**

MedAgent implements a **Write-Once-Read-Many (WORM)** compatible audit chain. Each interaction in a session generates a SHA-256 hash that includes the hash of the *previous* interaction. This creates a verifiable chronological chain, ensuring that medical history cannot be tampered with without detection.

### **Production-Grade Observability**

The system is fully instrumented for clinical monitoring:

- **Prometheus Metrics**: Real-time tracking of Request Latency, Error Rates, Model Usage, and Critical Escalations.
- **OpenTelemetry Tracing**: Granular span tracking across the entire agentic pipeline.
- **Middleware Logging**: Automatic monitoring of every API request for performance bottlenecks.

### **Multimodal Vision Diagnostics**

- **Supported Formats**: JPG, PNG, WEBP, and medical-standard **DICOM (.dcm)**.
- **Clinical Scopes**: Bone Fractures, Chest X-rays, MRI anomalies, Skin pathologies, and Lab Reports.

---

## 🧑‍⚕️ 4. Feature Highlights (9-Tab UI Hub)

The Streamlit-based **Global Hub** provides a comprehensive medical dashboard:

1. **💬 Consult**: Multi-agent interaction with ToT reasoning and "Second Opinion" requests.
2. **🔬 Image Analysis**: Multimodal scan processing with confidence scoring.
3. **🧪 Labs**: Dedicated pathology hub for interpreting laboratory values (WBC, Hb, Glucose, etc.).
4. **📅 Appointments**: Secure scheduling and Google Calendar synchronization.
5. **💊 Meds**: Active medication tracker with digital dosage reminders.
6. **📚 Education**: Generative hub for evidence-based medical summaries and condition backgrounds.
7. **📜 History**: Longitudinal medical memory with PDF/Image report exports.
8. **🛡️ Privacy**: Data rights management, accessibility toggles, and secure data porting (CSV).
9. **🔑 Admin**: Command center for human review, A/B testing, and system health metrics.

---

## 🛠️ 5. Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Logic & Orchestration** | LangChain, LangGraph, Python 3.9+ |
| **LLM Intelligence** | GPT-4o family, GPT-o1-preview (ToT Fallback) |
| **Vector Engine** | FAISS (Local Medical Guidelines Index) |
| **Persistence** | SQLite with SQLAlchemy (Bilingual Support EN/AR) |
| **Security** | AES-256 (Fernet), Bcrypt Hashing, JWT (JOSE) |
| **Observability** | Prometheus, OpenTelemetry, Python Logging |
| **UI Framework** | Streamlit (High-Aesthetics Modern Design) |

---

## 🚀 6. Setup & Installation

### **Prerequisites**

- OpenAI API Key (High-tier required for ToT and Vision).
- Python 3.9+ Environment.

### **Step-by-Step Launch**

1. **Clone & Install**:

    ```bash
    git clone https://github.com/MohamedMetawea/MedAgent.git
    pip install -r requirements.txt
    ```

2. **Environment Configuration**: Create a `.env` file with the following:

    ```env
    OPENAI_API_KEY=sk-...
    DATA_ENCRYPTION_KEY=... (Fernet key)
    JWT_SECRET_KEY=... (Random hex)
    ADMIN_API_KEY=... (For admin routes)
    AUDIT_SIGNING_KEY=... (For evidence export)
    INIT_RAG_ON_START=true
    ```

3. **Pre-flight Checks & Migration**:
    The system includes a mandatory startup check. If secrets are missing, it will block production routes for safety.

    ```bash
    python tests/pre_launch_check.py
    ```

4. **Unified Startup**:

    ```bash
    python run_system.py
    ```

---

## 🛡️ 7. Security & Privacy Compliance

- **End-to-End Encryption**: All PHI (Patient Health Information) is encrypted at rest using AES-256.
- **PII Scrubbing**: The Privacy Layer automatically redacts personal identifiers from agent logs.
- **Audit Trails**: Every agent decision is signed and hashed for forensics.
- **RBAC**: Strict role enforcement (Patient vs. Doctor vs. Admin).

---

## ⚖️ 8. Legal Disclaimer

*This system is a high-fidelity AI simulation developed as a graduation project. It is **NOT** a substitute for professional medical advice, diagnosis, or treatment. It is intended for research and educational purposes only. Always consult a licensed healthcare professional for medical decisions.*

---
**MedAgent: Bridging GenAI and Clinical Excellence.**  
*Empowering Healthcare with Autonomous Intelligence.*
