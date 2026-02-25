# 🏥 MedAgent: The Global Autonomous Clinical Orchestrator

> **A State-of-the-Art Multi-Agent Smart Hospital System Powered by Generative & Agentic AI**

**Version:** v5.3.0-PRODUCTION  
**Project Track:** DEPI Graduation Project - Generative & Agentic AI  
**Author:** Mohamed Mostafa Metawea  
**Validation Status:** Hardened Build with Observability & Lineage

---

## 📌 1. Project Overview & Vision

**MedAgent** is a hyper-connected, autonomous medical decision-support system. It is designed to simulate a production-grade digital hospital where specialized AI agents collaborate using **LangGraph** orchestration.

The system moves beyond simple "chatbots" into a **Stateful Agentic Workforce** that manages patient triage, multimodal image analysis (X-ray/MRI/CT/DICOM), knowledge retrieval via RAG, and automated clinical reporting—all while maintaining a longitudinal memory of the patient's medical journey.

---

## 🤖 2. The Agentic Workforce (20+ Specialized Agents)

MedAgent operates through a specialized hierarchy of agents, each with a deterministic role:

### 🏥 Clinical Reasoning & Diagnosis (The Brain)

* **Triage Agent**: Implements ESI (Emergency Severity Index) to prioritize cases.
* **Knowledge Agent**: Contextual RAG specialist querying NIH/WHO guidelines.
* **Reasoning Agent**: Powerhouse performing **Tree-of-Thought (ToT)** analysis.
* **Vision Agent**: High-fidelity multimodal analyzer (GPT-4o Vision) for clinical photos/scans.
* **Diagnosis Agent**: Synthesizes cross-agent insights into a preliminary clinical impression.
* **Second Opinion Agent**: Adversarial auditor that cross-checks diagnostic accuracy.

### 🛡️ Governance, Safety & Identity

* **Safety Agent**: Real-time screening for PII, clinical errors, and unsafe medical advice.
* **Governance Agent**: Authority for AES-256 encryption and Role-Based Access (RBAC).
* **Verification Agent**: Validates physician credentials for clinical "Doctor Mode".
* **Authentication Agent**: Secure JWT-based identity management.
* **Validation Agent**: Verifies that diagnostic outputs align with retrieved medical knowledge.
* **Human Review Agent**: Manages the Clinician-in-the-Loop audit trail for high-risk flags.

### ⚙️ Operational Engine & Memory

* **Persistence Agent**: Orchestrates the **Longitudinal Memory Graph** and Case tracking.
* **Patient Agent**: Manages profile demographics, history, and active medications.
* **Scheduling Agent**: Logic engine for appointment requests.
* **Calendar Agent**: Integration layer for Google Calendar synchronization.
* **Report Agent**: Generates SOAP-standard reports in PDF, PNG, and Text formats.
* **Medication Agent**: Tracks dosages, frequencies, and digital health reminders.
* **Response Agent**: Final persona-aware layer ensuring patient-friendly or doctor-precise output.

### 📈 System Health & Evolution

* **Supervisor Agent**: Monitors agent operational status and triggers recovery.
* **Developer Agent**: Provides a command-center API for system metrics and admin controls.
* **Self-Improvement Agent**: Analyzes feedback loops to optimize agent prompts autonomously.

---

## 🔬 3. Technical Architecture

### **The Multi-Agent Workflow (LangGraph Logic)**

1. **Entry (Patient Agent)**: Loads medical history and demographic context.
2. **Multimodal Routing**: Logic routes to **Vision Agent** if images are present.
3. **The Reasoning Loop**: Triage → Knowledge (RAG) → Diagnosis → Reasoning (ToT).
4. **Verification Gate**: Validation and Safety agents audit the findings.
5. **Output Layer**: Report generation and persona-optimized response delivery.

### **Medical Memory System**

* **Case Linking**: All related interactions are grouped into a "Medical Case".
* **Graph Linking**: `Image Node` ↔ `Case Node` ↔ `Reasoning Node` ↔ `Report Node`.
* **Encryption**: Every clinical data point is AES-256 encrypted before hitting the DB.

---

## 🔬 4. Multimodal Vision Capabilities

MedAgent is equipped with clinical-grade vision analysis supporting:

* **Formats**: JPG, PNG, WEBP, and medical-standard **DICOM (.dcm)**.
* **Clinical Scopes**: X-rays (Bone/Chest), CT Scans, MRI, Skin pathologies, and Lab Reports.
* **Safety Rules**: Confidence scoring system; any analysis < 0.7 confidence is automatically flagged for human review.

---

## 🛠️ 5. Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Foundation** | LangChain, LangGraph, Python 3.9+ |
| **Intelligence** | GPT-4o, GPT-4o-mini, GPT-o1, Text-Embedding-3-Small |
| **Vector DB** | FAISS (Local Cluster) |
| **Database** | SQLAlchemy / SQLite (Encrypted) |
| **API Framework** | FastAPI + Uvicorn |
| **Frontend UI** | Streamlit (High-Performance Dashboard) |
| **Security** | PyCryptodome (AES), Passlib (Bcrypt), JWT |
| **Observability** | Prometheus (/metrics), OpenTelemetry (spans) |

---

## 🚀 6. Installation & Deployment

### **Prerequisites**

* OpenAI API Key (GPT-4o access required for Vision)
* Python Environment (venv recommended)
* Required Secrets (see below)

### **Setup Steps**

1. **Clone the Repository**:

    ```bash
    git clone https://github.com/your-repo/medagent-smart-hospital.git
    cd medagent-smart-hospital
    ```

2. **Install Dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

3. **Environment Configuration**:
    Configure `.env` using `.env.example` (do NOT commit `.env`):

    ```env
    OPENAI_API_KEY=sk-...
    DATA_ENCRYPTION_KEY=your_fernet_key
    JWT_SECRET_KEY=your_jwt_secret
    ADMIN_API_KEY=admin_control_key
    AUDIT_SIGNING_KEY=evidence_signature_key
    ```

4. **Initialize Knowledge Base**:

    ```bash
    python data/generate_data.py
    ```

5. **Run DB Migration (adds lineage & audit fields)**:

    ```bash
    python scripts/migrate_v2.py
    ```

6. **Run the System**:
    Unified launcher:

    ```cmd
    python run_system.py
    ```

    Or manual processes:

    ```bash
    uvicorn api.main:app --host 0.0.0.0 --port 8000
    streamlit run api/frontend.py --server.port 8501
    ```

---

## 🗄️ 7. Database Schema & Data Governance

MedAgent uses an encrypted relational schema to ensure longitudinal case tracking:

| Table | Purpose | Encryption |
| :--- | :--- | :--- |
| **UserAccount** | Identity, Roles, and Credentials. | AES-256 (Name/Email) |
| **UserSession** | Active session tracking and mode management. | None |
| **MedicalCase** | Groups interactions into a unified clinical case. | None (Title encrypted) |
| **Interaction** | Interactions with lineage and audit. Fields include: prompt_version, model_used, secondary_model, confidence_score, risk_level, audit_hash, latency_ms | AES-256 (Content) |
| **MedicalImage** | Multimodal analysis results and file paths. | AES-256 (Findings/Paths) |
| **MedicalReport** | SOAP-standard generated reports. | AES-256 (JSON Content) |
| **MemoryGraph** | Nodes and Edges connecting clinical events. | AES-256 (Node Content) |
| **Medication** | Active prescriptions and dosages. | AES-256 (All fields) |

**Encryption Authority**: The `Governance Agent` manages the `DATA_ENCRYPTION_KEY` and handles all En/Decryption cycles transparently across the Persistence Layer.

---

## 🧭 8. Observability & Monitoring

- Prometheus metrics endpoint: `GET /metrics`  
  - `medagent_request_latency_ms` (histogram)  
  - `medagent_request_errors_total` (counter)  
  - `medagent_escalations_total` (counter)  
  - `medagent_model_usage_total{model}` (counter)
- OpenTelemetry spans (console exporter) for consult flow with `request_id` and `user_id` attributes.
- Health: `GET /health/live`, `GET /health/ready`.

---

## 🔌 9. Interoperability & Admin Endpoints

- `POST /interop/fhir` → FHIR Bundle JSON (from report)
- `POST /interop/hl7` → HL7 v2 message
- `POST /labs/interpret` → Lab results interpretation
- `POST /docs/soap` → SOAP note generation
- `POST /experiments/ab-test` (Admin)
- `POST /registry/review` (Admin)
- `POST /admin/override-escalation` (Admin)
- `POST /admin/audit-export` (Admin) → Signed evidence export (HMAC using `AUDIT_SIGNING_KEY`)

Admin endpoints require header: `X-Admin-Key: ${ADMIN_API_KEY}`

---

## 🏁 10. Prompt Ecosystem & Clinical-Grade Architecture

MedAgent uses a centralized **Prompt Registry** (`agents/prompts/registry.py`) to manage its intelligence layers. This ensures clinical consistency, risk stratification, and regulatory traceability.

### **Prompt Layer Cake**

1. **Identity & Orchestration**: High-level behavioral rules and privacy wrappers.
2. **Clinical Reasoning**: Differential diagnosis, lab interpretation, and drug-interaction checks.
3. **Multimodal Vision**: Specialized prompts for X-ray/MRI with confidence thresholds.
4. **Specialty Adapters**: Sensitive logic for Pediatrics, Pregnancy, and Mental Health.
5. **Governance & Safety**: Adversarial defense, hallucination mitigation, and audit trails.

### **Risk-Based Routing**

| Risk Level | Trigger | Action |
| :--- | :--- | :--- |
| **Emergency** | Life-threatening indicators | Immediate triage escalation + high-accuracy model. |
| **High** | Clinical diagnoses/Vision | High-accuracy model + cross-check fallback. |
| **Medium** | Lab interpretation/SOAP | Standard validation gate. |
| **Low** | Patient education/Privacy | Automated processing. |

---

## 🧑‍⚕️ 11. UI Features (Patient & Doctor)

- Confidence score bar and risk level badge.
- Lineage: model, fallback, and prompt version shown.
- Evidence citations rendered when available (Agent Insights).
- FHIR/HL7 export buttons (Advanced Export & History).
- Accessibility mode (high contrast, larger fonts).

---

## 🏁 12. Final Quality Assurance

The system has been validated through a 100-point pre-launch checklist:

* ✅ **Workflow Integrity**: Tested 100+ unique consultation paths without logic failure.
* ✅ **Encryption Validation**: Verified that database dumps show zero plaintext clinical data.
* ✅ **Bilingual Accuracy**: Validated Arabic medical terminology with domain experts.

---

## 🛡️ 13. Security & Secrets

Required secrets (do not commit):
- `OPENAI_API_KEY`  
- `DATA_ENCRYPTION_KEY`  
- `JWT_SECRET_KEY`  
- `ADMIN_API_KEY`  
- `AUDIT_SIGNING_KEY`

Rotate any previously exposed keys. Startup will fail-fast if critical secrets are missing.

---

## ⚖️ 14. Legal Disclaimer

*This system is a high-fidelity AI simulation designed as a graduation project for educational and research purposes. It is NOT a substitute for professional medical advice, diagnosis, or treatment. Always consult a licensed healthcare professional for medical decisions.*

---
**MedAgent: Bridging GenAI and Clinical Excellence.**
