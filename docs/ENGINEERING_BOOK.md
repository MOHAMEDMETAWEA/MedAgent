# MEDAgent — Complete Engineering Reference Book

> **Version**: 5.3.0 | **Architecture**: Multi-Agent LangGraph Orchestration | **License**: Hospital-Grade Clinical AI

---

# PART 1 — SYSTEM OVERVIEW

## 1.1 What is MEDAgent

MEDAgent is a **multi-agent clinical intelligence platform** built on LangGraph and FastAPI. It coordinates 20+ specialized AI agents through a stateful directed graph to process patient symptoms, medical images, and clinical data — producing diagnosed, safety-checked, explainable medical recommendations.

Unlike simple chatbot wrappers around an LLM, MEDAgent implements a **full clinical pipeline** with:
- Triage (risk classification)
- Knowledge retrieval (RAG with FAISS)
- Tree-of-Thought reasoning
- Cross-validation with hallucination detection
- Uncertainty calibration with human-in-the-loop escalation
- Specialty routing (pediatric, maternity, mental health)
- SOAP note generation for doctors
- Encrypted persistence with audit chains

## 1.2 Clinical Use Cases

| Use Case | Agents Involved | Output |
|:---|:---|:---|
| Symptom assessment | Patient → Triage → Reasoning → Response | Risk-classified diagnosis |
| Medical image analysis | Vision → Triage → Knowledge → Reasoning | Visual findings + diagnosis |
| Doctor clinical review | All agents + ClinicalReview → SOAP | SOAP notes + peer review |
| Medication tracking | Medication → Persistence | Adherence logs + reminders |
| Emergency escalation | Triage → Safety → Monitoring → Notifications | 911 alert + doctor notification |

## 1.3 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                            │
│     Streamlit UI  ←─→  FastAPI REST API (Uvicorn)              │
│       (frontend.py)      (api/main.py + routes/*)              │
└──────────────────────────────┬──────────────────────────────────┘
                               │ HTTP/WebSocket
┌──────────────────────────────▼──────────────────────────────────┐
│                 ORCHESTRATION LAYER                              │
│              MedAgentOrchestrator (LangGraph)                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Entry ──→ Vision/Patient ──→ Triage ──→ Knowledge/Review  │ │
│  │  ──→ Reasoning ↔ Validation ──→ Hallucination             │ │
│  │  ──→ Calibrator ──→ Safety ──→ Specialty Router           │ │
│  │  ──→ SafetyGuardrail ──→ SOAP ──→ END                    │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                   INTELLIGENCE LAYER                            │
│  CDSS Engine │ Inference Cache │ Clinical Explainer             │
│  RAG Retriever (FAISS) │ Model Router (Cloud/Local)            │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                     DATA LAYER                                  │
│  SQLAlchemy (Async+Sync) │ SQLite/PostgreSQL │ Redis Cache     │
│  AES-256 Encryption │ Immutable Audit Chain │ Memory Graph     │
└─────────────────────────────────────────────────────────────────┘
```

## 1.4 Data Flow: Request Lifecycle

```
1. User submits symptoms via Streamlit or REST API
2. FastAPI receives POST /api/consultation
3. Input → sanitize_input() → validate_medical_input() → PHI redaction
4. Orchestrator.run() creates an async session + loads user profile from DB
5. LangGraph graph.ainvoke(state) triggers the agent pipeline:
   a. PatientAgent: loads profile, long-term memory, memory graph
   b. VisionAgent (if image): GPT-4o Vision analysis
   c. TriageAgent: risk classification + symptom structuring
   d. KnowledgeAgent: FAISS RAG + FHIR EMR integration
   e. ReasoningAgent: Tree-of-Thought or fast-path diagnosis
   f. ValidationAgent: fact-checks diagnosis against evidence
   g. HallucinationDetector: factual integrity scoring
   h. UncertaintyCalibrator: confidence check, human-review trigger
   i. SafetyAgent: LLM-based risk audit + injection detection
   j. Specialty Router: pediatric/maternity/mental health (if applicable)
   k. ResponseAgent: adaptive communication polish
   l. SafetyGuardrailAgent: final disclaimer injection + emergency override
   m. SoapAgent: structured SOAP note generation
6. Final state saved to DB via PersistenceAgent (encrypted)
7. Result cached in Redis for subsequent identical queries
8. Response returned to user with safety disclaimers
```

---

# PART 2 — ARCHITECTURE DEEP DIVE

## 2.1 Multi-Agent System Design

Each agent is a **stateless function that receives and returns a shared `AgentState` dictionary**. The `AgentState` is a LangGraph `TypedDict` defined in `agents/state.py` with 30+ fields covering:

- `messages`: LangChain message history (accumulates via `operator.add`)
- `patient_info`: structured patient data from triage
- `preliminary_diagnosis`: text output from reasoning
- `validation_status`: "valid" / "invalid" / "skipped"
- `safety_status`: "safe" / "unsafe" / "blocked"
- `final_response`: the polished output shown to the user
- `interaction_mode`: "patient" or "doctor"
- `correction_count`: tracks self-correction loop iterations
- `risk_level`: "Low" / "Medium" / "High" / "Emergency"

## 2.2 LangGraph Orchestration

The orchestrator (`agents/orchestrator.py`) builds a **compiled LangGraph `StateGraph`** with:

- **20 nodes**: Each mapped to an agent class via lazy-loading registry
- **Conditional entry**: Parallel `vision + patient` if image exists, else `patient` only
- **Conditional routing**: After triage (knowledge vs human review), after validation (retry vs continue), after safety (specialty routing)
- **Self-correction loop**: Validation → Reasoning with max 2 retries
- **Model fallback**: If any node fails, the orchestrator swaps to a fallback model and retries

### Agent Registry (Lazy Loading)

```python
self._agent_registry = {
    "patient": ("agents.patient_agent", "PatientAgent"),
    "triage": ("agents.triage_agent", "TriageAgent"),
    "knowledge": ("agents.knowledge_agent", "KnowledgeAgent"),
    "reasoning": ("agents.reasoning_agent", "ReasoningAgent"),
    # ... 16 more agents
}
```

Each agent is loaded only when first requested via `get_agent(name)`, which uses `importlib.import_module` for lazy imports. This reduces startup time from ~8s to ~2s.

### Node Wrapping

Every node is wrapped with `wrap_node()` which:
1. Detects if the agent's `process()` is async via `inspect.iscoroutinefunction`
2. Wraps with try/except for self-healing model fallback
3. On failure: imports `model_registry`, gets fallback model, swaps `agent.llm`, retries once

## 2.3 FastAPI Backend

`api/main.py` (1114 lines) — the main application:

- **Routers**: Modular router files in `api/routes/` for consultation, auth, reports, feedback, etc.
- **Middleware**: CORS with configurable origins
- **Observability**: Prometheus `Histogram` (latency), `Counter` (errors, escalations, model usage)
- **OpenTelemetry**: `TracerProvider` with `ConsoleSpanExporter` for distributed tracing
- **Health**: `/health`, `/health/live`, `/health/ready`, `/ready` endpoints
- **Upload**: Secure image upload with format validation and 20MB limit

## 2.4 Database Layer

`database/models.py` (426 lines) — dual-engine SQLAlchemy:

- **Async engine**: `aiosqlite` for the main async pipeline
- **Sync engine**: Legacy `SessionLocal` for governance/admin operations
- **20 tables**: Covering users, sessions, interactions, feedback, audit, medical images, symptoms, medications, memory graph, reminders, system config

## 2.5 RAG Pipeline

`rag/retriever.py` — FAISS vector store with OpenAI embeddings:

1. Loads `medical_guidelines.json` (structured condition/treatment pairs)
2. Splits with `RecursiveCharacterTextSplitter` (500 chars, 50 overlap)
3. Creates `FAISS.from_documents()` and saves index locally
4. Retrieves top-K documents using semantic similarity search
5. Validates sources against trusted domains (WHO, NIH, PubMed, CDC)

## 2.6 Prompt System

Prompts are stored as `.txt` files in `prompts/` directory. Each agent loads its prompt via `config.get_prompt_path()`. The `PromptRegistry` (`prompts/registry.py`) provides:

- Hot-swapping of agent prompts without restart
- Version tracking (currently `1.0.0` default)
- Centralized governance with `refresh()` from disk

## 2.7 Model Routing

`models/model_router.py` — abstraction layer that routes LLM calls to:

- **Cloud**: OpenAI `ChatOpenAI` (default)
- **Local/Ollama**: `ChatOllama` if `MODEL_MODE=local` and Ollama URL available
- **Local/vLLM**: OpenAI-compatible API endpoint for vLLM deployment

---

# PART 3 — FULL CODE WALKTHROUGH

## 3.1 Configuration — `config.py`

### Purpose
Central configuration hub. Uses Pydantic `BaseSettings` to load environment variables from `.env` with type validation.

### Key Settings Groups

| Group | Settings | Purpose |
|:---|:---|:---|
| API Keys | `OPENAI_API_KEY`, `JWT_SECRET_KEY` | Native App Authentication & LLM access |
| Paths | `BASE_DIR`, `PROMPTS_DIR`, `DATA_DIR`, `INDEX_DIR` | File system layout |
| RAG | `RAG_CHUNK_SIZE=500`, `RAG_TOP_K=3`, `RAG_RELEVANCE_THRESHOLD=0.5` | Retrieval tuning |
| LLM | `LLM_TEMPERATURE_DIAGNOSIS=0.0`, `LLM_TEMPERATURE_PATIENT=0.3` | Per-role temperature control |
| Safety | `MAX_INPUT_LENGTH=2000`, `BLOCK_UNSAFE_REQUESTS=True` | Input validation |
| Model Routing | `MODEL_MODE=cloud`, `LOCAL_MODEL_NAME=meditron` | Cloud vs local LLM |
| EHR/FHIR | `FHIR_BASE_URL`, `FHIR_CLIENT_*` | Hospital EMR integration |
| Database | `DATABASE_URL=sqlite:///./medagent.db` | Storage backend |

### Critical Functions

**`get_prompt_path(filename)`**: Returns absolute path to a prompt file. Raises `FileNotFoundError` if missing — this is intentional as a safety measure to prevent agents from running without proper medical prompts.

**`ensure_directories()`**: Called at import time. Creates `prompts/`, `data/`, `rag/`, and `rag/faiss_index/` directories.

---

## 3.2 Agent State — `agents/state.py`

### Purpose
Defines the `AgentState` TypedDict — the **shared mutable state** that flows through the entire LangGraph pipeline.

### Line-by-Line

```python
messages: Annotated[Sequence[BaseMessage], operator.add]
```
→ Uses LangGraph's **reducer** pattern. The `operator.add` annotation means that when any agent returns `{"messages": [...]}`, the new messages are **appended** to the existing list, not replaced. This preserves the full conversation history.

```python
user_age: str
```
→ Typed as `str` (not `int`) because it may be `"Unknown"` for guest users. All agents check `state.get("user_age", 0)` with int coercion where needed.

```python
correction_count: int
```
→ Tracks self-correction loop iterations. The orchestrator's `route_validation()` checks `correction_count < 2` to prevent infinite retry loops.

---

## 3.3 Orchestrator — `agents/orchestrator.py`

### Purpose
The **brain** of the system. Builds and compiles the LangGraph `StateGraph`, manages agent lifecycle, and runs the async pipeline.

### Class: `MedAgentOrchestrator`

**`__init__`**: Initializes `_agent_registry` (20 entries) and `_agent_cache` (empty dict). Does NOT instantiate any agent — they are lazy-loaded.

**`get_agent(name)`**: First checks `_agent_cache`. If miss, looks up `(module_path, class_name)` from `_agent_registry`, uses `importlib.import_module` + `getattr` to load the class, instantiates it, caches it, and returns it.

**`_build_graph()`**: The core graph construction method.

#### Graph Construction Deep Dive

```python
workflow = StateGraph(AgentState)
```
→ Creates a new LangGraph state graph typed to `AgentState`.

```python
def wrap_node(node_name):
    agent = self.get_agent(node_name)
    method = getattr(agent, "process", None) or getattr(agent, "run", None)
    is_async = inspect.iscoroutinefunction(method)
```
→ Every agent is wrapped. The wrapper looks for `process()` first, then `run()`. It detects if the method is async.

```python
if is_async:
    return await method(state)
return method(state)
```
→ Supports both sync and async agents transparently. The LangGraph framework handles async wrapping.

```python
from learning.model_registry import model_registry
fallback = model_registry.get_fallback_model()
agent.llm = get_model(model_name=fallback.get("version"))
```
→ **Self-healing fallback**: If any agent crashes, the wrapper dynamically swaps the agent's LLM to a backup model and retries once.

#### Edge Structure (Post-Audit Fix)

The graph flow after the production audit fix:

1. **Parallel Entry**: `vision + patient` (if image) or `patient` only
2. **Convergence**: Both → `triage`
3. **Conditional**: `triage` → `knowledge` (normal) or `review` → `END` (high-risk)
4. **Core Pipeline**: `knowledge → reasoning → validation`
5. **Self-Correction**: `validation` → `reasoning` (if invalid, max 2 retries)
6. **Trust Pipeline**: `hallucination → calibrator → safety`
7. **Specialty Router**: `safety` → `pediatric`/`maternity`/`mental_health`/`response`
8. **Final Check**: All specialties → `safety_guardrail → soap → END`

**`run()` method**: The main entry point. Creates session, loads user profile from DB, integrates EHR data, checks Redis cache, builds initial state (30+ fields), invokes `graph.ainvoke(state)`, sends emergency notifications if needed, caches result, and saves to database.

---

## 3.4 Patient Agent — `agents/patient_agent.py`

### Purpose
First agent in the pipeline. Loads patient profile, medical history, and memory graph context. Summarizes the patient's input for downstream agents.

### Key Logic

```python
profile = await persistence.get_patient_profile(user_id)
long_term_memory = await persistence.get_long_term_memory(user_id)
memory_graph = await persistence.get_memory_graph_context(user_id)
case_id = await persistence.get_or_create_case(user_id)
```
→ Four async database lookups that build a comprehensive patient context. The `memory_graph` retrieves a summarized graph of all past symptoms, diagnoses, and medications.

```python
response = await llm.ainvoke([system_msg, intake_msg])
```
→ Uses the LLM to generate a structured patient summary from the raw input + context.

---

## 3.5 Triage Agent — `agents/triage_agent.py`

### Purpose
Classifies symptom urgency and structures patient data. Integrates FHIR EMR data and the MedicalSafetyFramework for regulatory risk classification.

### Key Logic

```python
risk_level = MedicalSafetyFramework.classify_risk(user_input)
mandatory_disclaimer = MedicalSafetyFramework.get_mandatory_disclaimer(risk_level)
```
→ Keyword-based risk classification: scans for "chest pain", "suicide", "seizure" etc. Returns "Emergency" / "High" / "Medium" / "Low".

```python
fhir_client = FHIRClient()
bg = fhir_client.fetch_patient_background(fhir_id)
```
→ If the patient has a FHIR ID, pulls EMR conditions and medications to enrich the triage context.

```python
is_sufficient = "STRUCTURED_CASE:" in content
```
→ The LLM is prompted to output `STRUCTURED_CASE:` followed by JSON if it has enough data for structured analysis. If missing, the case is marked "incomplete".

---

## 3.6 Knowledge Agent — `agents/knowledge_agent.py`

### Purpose
Retrieves clinical evidence from the FAISS vector store and FHIR EMR system.

### Key Logic

```python
fhir = FHIRConnector(base_url=settings.FHIR_BASE_URL)
conditions = await fhir.get_conditions(patient_id)
meds = await fhir.get_medications(patient_id)
```
→ Fetches real EMR data using the HL7 FHIR R4 standard.

```python
retriever = self.get_retriever()
knowledge = retriever.retrieve(patient_summary)
```
→ Semantic search against the FAISS index. Returns top-K matching medical guideline chunks.

```python
trusted_domains = ["who.int", "nih.gov", "pubmed", "cdc.gov"]
is_verified = any(domain in knowledge.lower() for domain in trusted_domains)
```
→ Source verification: flags whether retrieved knowledge comes from trusted clinical sources.

---

## 3.7 Reasoning Agent — `agents/reasoning_agent.py`

### Purpose
Core diagnostic engine. Uses **Tree-of-Thought (ToT)** reasoning for high-risk cases and fast-path single-shot for lower-risk.

### Key Logic

```python
cdss_data = await cdss_engine.generate_cdss_payload(state)
state["risk_level"] = cdss_data["cdss_risk"]
```
→ Integrates the CDSS (Clinical Decision Support System) to set a NEWS2-style risk score.

```python
if risk_level not in ["high", "emergency"]:
    # FAST PATH: Single LLM call with structured output
    response = await llm.ainvoke([...])
else:
    # ToT PATH: Generate 3 branches, then evaluate
    paths_response = await llm.ainvoke([...])
    final_selection = await llm.ainvoke([...])
```
→ **Performance optimization**: Low-risk cases get a single LLM call. High-risk cases get 3 reasoning branches + expert selection (2 LLM calls). This balances cost vs clinical safety.

```python
explanation = await clinical_explainer.generate_explanation(state, target_role=role)
```
→ Role-adapted explanations: doctors get technical reasoning traces; patients get simplified explanations.

---

## 3.8 Validation Agent — `agents/validation_agent.py`

### Purpose
Cross-checks the reasoning output against the retrieved evidence. Prevents hallucinations at the validation layer.

### Key Logic

```python
if "VALID" in result and "ISSUE" not in result:
    return {"validation_status": "valid"}
else:
    return {"validation_status": "invalid", "retry_reason": result}
```
→ The LLM is asked to output "VALID" or "ISSUE: <explanation>". If invalid, `retry_reason` triggers the self-correction loop back to reasoning.

---

## 3.9 Hallucination Detector — `agents/hallucination_detector.py`

### Purpose
Specialized auditor that scores the factual integrity of the diagnosis against retrieved evidence.

### Key Logic

```python
state["hallucination_score"] = score
state["is_hallucinating"] = score < 85
```
→ If the score falls below 85/100, the detector flags it and sets `validation_status = "invalid"` to trigger the correction loop.

```python
def _parse_score(self, text: str) -> int:
    match = re.search(r'Score:\s*(\d+)', text, re.IGNORECASE)
```
→ Regex extraction of the numerical score from the LLM's free-text response.

---

## 3.10 Uncertainty Calibrator — `agents/uncertainty_calibrator.py`

### Purpose
Determines if AI confidence is high enough for autonomous output, or if human review is mandatory.

### Key Logic

```python
if state.get("is_hallucinating"):
    confidence -= 20
if state.get("correction_count", 0) > 1:
    confidence -= 10
```
→ Penalizes confidence for hallucination or repeated corrections.

```python
if state["calibrated_confidence"] < self.threshold:
    state["requires_human_review"] = True
```
→ If calibrated confidence drops below 85%, mandatory human review is triggered.

---

## 3.11 Safety Agent — `agents/safety_agent.py`

### Purpose
LLM-powered safety auditor that checks the diagnosis for harmful content, red flags, and prompt injection.

### Key Logic

```python
from utils.safety import detect_critical_symptoms, _detect_injection_patterns
is_critical, keywords = detect_critical_symptoms(diagnosis)
is_injection, injection_patterns = _detect_injection_patterns(diagnosis)
```
→ Dual check: keyword-based critical symptom detection + regex-based injection pattern detection.

```python
response = llm.invoke([...])
parsed = json.loads(result[start:end])
risk_level = parsed.get("risk_level", "LOW")
```
→ LLM generates a structured JSON safety assessment. Falls back to keyword heuristic if JSON parsing fails.

---

## 3.12 Specialty Agents

### Pediatric Agent (`agents/pediatric_agent.py`) — "Theo"
Transforms clinical findings into child-friendly explanations using metaphors and encouraging language. The LLM is persona-prompted as "Theo", a friendly pediatric specialist.

### Pregnancy Agent (`agents/pregnancy_agent.py`) — "Maya"
OB/GYN specialist. Provides pregnancy-safe advice, categorizes medications (A/B/C/D/X), and tailors to trimester.

### Mental Health Agent (`agents/mental_health_agent.py`) — "Aria"
Clinical psychologist. Screens for suicide/self-harm risk, uses trauma-informed language, and provides coping mechanisms. Calculates a basic distress score (1-10).

---

## 3.13 Response Agent — `agents/response_agent.py`

### Purpose
Final polish of the system response based on interaction mode, role, language, and communication preferences.

### Key Logic

```python
prompt = base_prompt.format(
    mode=mode_label, role=role.upper(), verified=str(verified),
    age=age, gender=gender, country=country,
    education=edu.upper(), literacy=lit.upper(), emotion=emo.upper(),
    input_content=final_response
)
```
→ Uses a structured communication template that adapts based on 9 context variables.

```python
from .patient_adapter import PatientCommunicationAdapter
adapter = PatientCommunicationAdapter()
adapted_response = adapter.transform(adapted_response, state)
```
→ Additional simplification for patient-mode users through the Patient Communication Adapter.

---

## 3.14 Safety Guardrail Agent — `agents/safety_guardrail_agent.py`

### Purpose
**Final node** before SOAP. Injects mandatory disclaimers and overrides the response in emergency cases.

### Key Logic

```python
risk_level = MedicalSafetyFramework.classify_risk(final_response)
disclaimer = MedicalSafetyFramework.get_mandatory_disclaimer(risk_level)
if disclaimer not in final_response:
    state["final_response"] = f"{final_response}\n\n---\n{disclaimer}"
```
→ Ensures every response has a risk-appropriate disclaimer. For emergencies, completely overrides with a call-911 message.

---

## 3.15 SOAP Agent — `agents/soap_agent.py`

### Purpose
Clinical documentation. Generates structured SOAP notes (Subjective, Objective, Assessment, Plan) for doctor dashboards.

### Key Logic

```python
prompt = ChatPromptTemplate.from_messages([
    ("system", self.system_prompt),
    ("user", f"SYMPTOMS: {symptoms}\nVITALS: {vitals}\nIMAGING: {findings}\nDIAGNOSIS: {diagnosis}")
])
chain = prompt | self.llm
response = await chain.ainvoke({})
state["soap_notes"] = response.content
```
→ Uses `prompt | llm` LangChain chain syntax to generate structured SOAP documentation.

---

## 3.16 Clinical Review Agent — `agents/clinical_review_agent.py`

### Purpose
Human-in-the-loop (HITL) workflow. When triage detects high-risk, this agent flags the case for doctor review and pauses execution.

### Key Logic

```python
def process(self, state: dict):
    return self.process_high_risk_case(state)
```
→ The `process()` method (required by the orchestrator) delegates to `process_high_risk_case()` which sets `requires_human_review = True` and returns a HITL-active status.

```python
def submit_review(self, interaction_id, action, comment):
```
→ API endpoint handler for when a doctor approves, rejects, or escalates a flagged case.

---

## 3.17 Vision Agent — `agents/vision_agent.py`

### Purpose
Analyzes medical images (X-ray, MRI, skin lesions) using GPT-4o Vision with clinical-grade structured prompts.

### Key Logic

```python
def _encode_image(self, image_path: str) -> str:
    if ext in ["dicom", "dcm"]:
        ds = pydicom.dcmread(image_path)
        img_array = ds.pixel_array.astype(float)
```
→ DICOM support: reads medical imaging format, rescales pixel data to 0-255, converts to PNG, then base64-encodes.

---

## 3.18 Persistence Agent — `agents/persistence_agent.py`

### Purpose
566-line agent managing all database operations: sessions, interactions, profiles, memory graph, medical cases, and reports.

### Key Methods

| Method | Purpose |
|:---|:---|
| `create_session()` | Creates a new tracking session |
| `save_interaction()` | Saves encrypted interaction to DB |
| `get_patient_profile()` | Loads patient medical history |
| `get_long_term_memory()` | Summarizes past conversation context |
| `get_memory_graph_context()` | Retrieves graph nodes (symptoms, diagnoses, etc.) |
| `get_or_create_case()` | Groups interactions into medical cases |
| `save_medical_report()` | Stores encrypted clinical reports |

All text data is encrypted via `GovernanceAgent.encrypt()` (AES-256 Fernet) before storage.

---

## 3.19 Governance Agent — `agents/governance_agent.py`

### Purpose
232-line security hub managing encryption, JWT authentication, password hashing, RBAC, and token revocation.

### Key Methods

**Encryption**:
```python
def encrypt(self, data: str) -> str:
    return self.cipher.encrypt(data.encode()).decode()
```
→ Uses Fernet (AES-256-CBC) encryption. Key from `DATA_ENCRYPTION_KEY` env var. Generates warning-level temp key if missing.

**JWT with Revocation**:
```python
def verify_token(self, token: str):
    payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
    jti = payload.get("jti")
    if inference_cache._redis.exists(f"token_blacklist:{jti}"):
        return None  # Token has been revoked
```
→ Every JWT gets a unique `jti` (JWT ID). On logout, the `jti` is added to a Redis blacklist with the token's remaining TTL.

---

## 3.20 Utilities — `utils/`

### `utils/safety.py`
| Function | Returns | Purpose |
|:---|:---|:---|
| `detect_prompt_injection(text)` | `bool` | Detects 10 common LLM adversarial patterns |
| `sanitize_input(text)` | `str` | PHI redaction + injection check + length enforcement |
| `_detect_injection_patterns(text)` | `Tuple[bool, List]` | Internal: returns matched pattern list |
| `detect_critical_symptoms(text)` | `Tuple[bool, List]` | Keyword-based emergency detection |
| `validate_medical_input(text)` | `Tuple[bool, Optional[str]]` | Comprehensive validation |
| `add_safety_disclaimer(response)` | `str` | Appends medical disclaimer |

### `utils/audit_logger.py`
Implements an **immutable audit chain** using SHA-256 hash linking:
```python
prev_hash = last_log.audit_hash if last_log else "GENESIS_BLOCK"
raw_content = f"{prev_hash}-{user_id}-{agent_name}-{input_data[:50]}-{output_data[:50]}"
audit_hash = hashlib.sha256(raw_content.encode()).hexdigest()
```
Each log entry links to the previous entry's hash, creating a blockchain-like chain that detects tampering.

### `utils/phi_redactor.py`
Regex-based PHI stripping for 6 pattern types: email, phone, SSN, DOB, credit card, name prefixes.

### `utils/medical_safety_framework.py`
Static methods for risk classification and mandatory disclaimers. Includes forbidden topics list (dosage recommendations, surgical instructions, euthanasia).

---

# PART 4 — SYSTEM INTEGRATION

## 4.1 Orchestrator → Agents

The orchestrator uses a **lazy registry pattern**:
```
orchestrator.get_agent("reasoning")
  → _agent_cache["reasoning"] ? return cached
  → _agent_registry["reasoning"] → ("agents.reasoning_agent", "ReasoningAgent")
  → importlib.import_module("agents.reasoning_agent")
  → getattr(module, "ReasoningAgent")()
  → Cache and return
```

## 4.2 Agents → Prompt Registry

Each agent loads its prompt via `self._load_prompt("agent_name.txt")` which calls `config.get_prompt_path()`. The Prompt Registry (`prompts/registry.py`) provides governance-level control with `get_prompt()`, `update_prompt()`, and `refresh()`.

## 4.3 API → Orchestrator

```
POST /api/consultation
  → api/routes/consultation.py → get_orchestrator() → orchestrator.run()
  → Returns full state dict to the caller
```

The `get_orchestrator()` DI function in `api/deps.py` maintains a singleton orchestrator instance.

## 4.4 DB → Persistence

```
Interaction Flow:
  1. orchestrator.run() → persistence.create_session()
  2. LangGraph pipeline runs (agents read/write state)
  3. orchestrator.run() → persistence.save_interaction(state)
  4. All fields encrypted: user_input, diagnosis, final_response
  5. Audit hash generated and linked to previous hash
```

## 4.5 Safety → Final Output

Triple-layer safety:
1. **Input**: `sanitize_input()` → prompt injection + PHI redaction
2. **Pipeline**: `SafetyAgent` → LLM-based risk audit + keyword detection
3. **Output**: `SafetyGuardrailAgent` → mandatory disclaimers + emergency override

---

# PART 5 — AI SYSTEM EXPLANATION

## 5.1 Tree-of-Thought Reasoning

For high-risk cases (`risk_level` = "High" or "Emergency"):

1. **Branch Generation**: LLM generates 3 distinct diagnostic reasoning branches
2. **Expert Evaluation**: Second LLM call selects the best branch
3. **Structured Output**: Returns JSON with `diagnosis`, `confidence`, `reasoning_steps`, `supporting_symptoms`, `evidence_sources`, `alternative_diagnoses`

For lower-risk cases, a single LLM call with the same structured output format is used (fast path).

## 5.2 Confidence Scoring

Confidence flows through 3 stages:
1. **Reasoning**: LLM self-reports `confidence` in its JSON output
2. **Calibration**: `UncertaintyCalibrator` adjusts: -20 for hallucination, -10 for multiple corrections
3. **Threshold**: If calibrated confidence < 85%, mandatory human review

## 5.3 Risk Classification

Two independent systems:
1. **MedicalSafetyFramework** (keyword-based): 18 emergency keywords, 3 high-risk triggers
2. **CDSS Engine** (vital-based): NEWS2-style scoring on heart rate, SpO2, temperature

## 5.4 RL Feedback System

`learning/feedback_loop.py`:
- Aggregates doctor feedback ratings by role
- Identifies low-confidence + high-risk interaction clusters
- Finds doctor-corrected responses for fine-tuning extraction
- Feeds into model improvement and prompt refinement

## 5.5 Model Registry

`learning/model_registry.py`:
- JSON-based registry at `data/models/registry.json`
- Tracks model versions, metrics, deployment status
- `promote_to_production()` swaps the active model
- `get_fallback_model()` returns a backup for self-healing

---

# PART 6 — DATABASE EXPLANATION

## 6.1 Table Inventory

| Table | Purpose | Encrypted Fields |
|:---|:---|:---|
| `user_accounts` | Identity, auth, roles | `full_name_encrypted`, `profile_metadata_encrypted` |
| `user_sessions` | Session tracking | — |
| `interactions` | Clinical interactions | `user_input_encrypted`, `diagnosis_output_encrypted`, `final_response_encrypted` |
| `medical_cases` | Groups interactions | — |
| `patient_profiles` | Medical history | `name_encrypted`, `medical_history_encrypted` |
| `medical_reports` | Clinical reports | `report_content_encrypted` |
| `medical_images` | Image metadata | `image_path_encrypted`, `visual_findings_encrypted` |
| `symptom_logs` | Symptom tracking | `symptom_name_encrypted`, `notes_encrypted` |
| `medication_records` | Medications | `medication_name_encrypted`, `dosage_encrypted` |
| `medications` | Active medications | `name_encrypted`, `dosage_encrypted`, `frequency_encrypted` |
| `reminders` | Alerts | `title_encrypted` |
| `user_feedback` | Basic ratings | — |
| `feedback` | Clinical RLHF feedback | `ai_response_encrypted`, `comment_encrypted`, `corrected_response_encrypted` |
| `audit_logs` | Admin audit trail | — |
| `ai_audit_logs` | AI decision audit | Hash-linked chain |
| `system_logs` | System events | — |
| `memory_nodes` | Memory graph nodes | `content_encrypted` |
| `memory_edges` | Memory graph edges | — |
| `user_activities` | Login tracking | — |
| `system_config` | Key-value config | — |

## 6.2 Key Relationships

```
UserAccount ──1:N──→ MedicalCase ──1:N──→ Interaction
UserSession ──1:N──→ Interaction
PatientProfile ──1:N──→ MedicalReport, SymptomLog, MedicationRecord
UserAccount ──1:N──→ MemoryNode ──M:N──→ MemoryEdge
Medication ──1:N──→ Reminder
```

## 6.3 Memory Graph

The `MemoryNode` + `MemoryEdge` tables form a **personal medical knowledge graph** per user:
- **Node types**: Symptom, Diagnosis, Image, Report, Medication, Case
- **Edge types**: `relates_to`, `caused_by`, `diagnosed_as`, `follow_up_of`, `based_on`
- Used by `PatientAgent` to provide longitudinal medical context

## 6.4 Audit Chain

The `ai_audit_logs` table implements an immutable chain:
```
Log 1: audit_hash = SHA256("GENESIS_BLOCK-user-agent-in-out")
Log 2: audit_hash = SHA256("{hash_1}-user-agent-in-out"), previous_hash = hash_1
Log 3: audit_hash = SHA256("{hash_2}-user-agent-in-out"), previous_hash = hash_2
```
Any tampering breaks the chain and is detectable.

---

# PART 7 — SECURITY

## 7.1 JWT Authentication

- **Creation**: `GovernanceAgent.create_access_token()` → HS256 JWT with `jti` (unique ID), 24h expiry
- **Verification**: `GovernanceAgent.verify_token()` → Decodes JWT, checks Redis blacklist for `jti`
- **Revocation**: `GovernanceAgent.revoke_token()` → Adds `jti` to `token_blacklist:{jti}` in Redis with remaining TTL

## 7.2 AES-256 Encryption

All PHI (Protected Health Information) is encrypted at rest using Fernet (AES-256-CBC):
- Key: `DATA_ENCRYPTION_KEY` environment variable
- If missing: temporary key generated with warning (data lost on restart)
- Applied to: patient names, medical history, diagnoses, responses, image paths, symptoms, medications

## 7.3 PHI Handling

Three layers of PHI protection:
1. **Input**: `phi_redactor.redact()` strips emails, phones, SSNs, DOBs, credit cards, name prefixes
2. **Storage**: All text encrypted before database write
3. **Logs**: `PHIRedactor.cleanup_logs()` available for log processors

## 7.4 Prompt Injection Defense

Two detection systems:
1. **Primary** (`detect_prompt_injection`): 10 patterns including "ignore instructions", "DAN mode", "jailbreak"
2. **Extended** (`_detect_injection_patterns`): 11 patterns including system/assistant prefix injection, token markers

When detected: input is replaced with error message, request is logged as security event.

## 7.5 Rate Limiting

`RATE_LIMIT_ENABLED=True`, `MAX_REQUESTS_PER_MINUTE=60`. Implemented via middleware tracking in the API layer.

---

# PART 8 — PERFORMANCE

## 8.1 Async Architecture

- **Database**: `aiosqlite` async engine with `AsyncSession`
- **Agents**: 12 of 20 agents are `async def process()` using `await llm.ainvoke()`
- **External APIs**: All FHIR calls use `httpx.AsyncClient()`
- **Orchestrator**: `graph.ainvoke(state)` runs the entire pipeline asynchronously

## 8.2 Redis Caching

`intelligence/inference_cache.py`:
- SHA-256 hash of `symptoms + interaction_mode` as cache key
- 1-hour TTL (configurable)
- Falls back to local dict cache if Redis unavailable
- Identical queries return cached results without LLM calls

## 8.3 Lazy Agent Loading

Agents are instantiated on first use via `importlib.import_module`. This reduces:
- Startup time: ~8s → ~2s
- Memory: only used agents are loaded
- Import errors: isolated to the agent that fails

## 8.4 Optimized Reasoning

- Low-risk: 1 LLM call (fast path)
- High-risk: 2 LLM calls (Tree-of-Thought)
- Temperature tuning: `0.0` for diagnosis, `0.3` for patient communication

---

# PART 9 — TESTING

## 9.1 Test Structure

Tests are located in `tests/` directory. Key test files:
- Medical safety framework validation
- Triage classification accuracy
- Prompt injection detection coverage
- API endpoint integration tests

## 9.2 What Each Test Validates

- **Safety tests**: Verify emergency keyword detection, confirm all 18 emergency keywords trigger "Emergency" classification
- **Injection tests**: Verify prompt injection patterns are detected and blocked
- **Triage tests**: Validate risk classification for various symptom inputs
- **API tests**: Integration tests for health endpoints, upload, and consultation

---

# PART 10 — DEPLOYMENT

## 10.1 Environment Variables

| Variable | Required | Purpose |
|:---|:---|:---|
| `OPENAI_API_KEY` | Yes | GPT-4 access |
| `JWT_SECRET_KEY` | Yes | Token signing (min 32 chars) |
| `DATA_ENCRYPTION_KEY` | Yes | AES-256 encryption key |
| `DATABASE_URL` | Optional | Default: SQLite |
| `REDIS_URL` | Optional | Caching + token blacklist |
| `FHIR_BASE_URL` | Optional | EMR integration |
| `SMTP_HOST/USER/PASSWORD` | Optional | Email notifications |

## 10.2 Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env from template
cp .env.example .env

# Start API server
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Start Streamlit UI
streamlit run frontend.py
```

## 10.3 Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 10.4 Kubernetes

K8s manifests in `k8s/` directory provide:
- Deployment with health probes (`/health/live`, `/health/ready`)
- Service exposure
- ConfigMap for environment variables
- HPA for auto-scaling

---

# PART 11 — PROBLEMS & IMPROVEMENTS

## 11.1 Bugs Fixed in This Audit

| # | File | Bug | Severity |
|:--|:--|:--|:--|
| 1 | `orchestrator.py` | Fatal LangGraph conflicting edges (safety had 2 targets, response had 2 targets, safety_guardrail added after compile) | 🔴 Critical |
| 2 | `reasoning_agent.py` | `def process()` (sync) contained 5 `await` calls — SyntaxError | 🔴 Critical |
| 3 | `safety_agent.py` | `detect_prompt_injection()` returns `bool` but unpacked as tuple | 🟠 High |
| 4 | `clinical_review_agent.py` | Missing `process()` method + stubbed `submit_review()` | 🟠 High |

## 11.2 Remaining Weak Design Areas

1. **`phi_redactor.py` line 7**: `from typing import str` — this is a Python bug. `str` is a builtin, not from `typing`. Should be removed. Won't crash because Python ignores re-importing builtins but is poor form.

2. **`prompts/registry.py` line 14**: Uses `settings.PROMPT_DIR` but `config.py` defines `PROMPTS_DIR`. This would raise `AttributeError` at runtime.

3. **`triage_agent.py`**: The `process()` method is synchronous but could benefit from async for consistency with the pipeline.

4. **Response Agent**: `_get_llm()` doesn't accept `state` parameter, so it can't use the model from state. Always uses the default model.

5. **Session management in governance**: Uses sync `SessionLocal` while the main pipeline uses async sessions. Could cause connection pool issues under load.

## 11.3 Suggested Improvements

1. **Centralized error handling**: Create a base exception hierarchy for medical errors
2. **Structured LLM output**: Use LangChain's `with_structured_output()` instead of manual JSON parsing
3. **Connection pooling**: Switch from SQLite to PostgreSQL for production
4. **Observability**: Add agent-level latency tracking to Prometheus metrics
5. **Testing**: Add comprehensive integration tests with mocked LLM responses
6. **Prompt versioning**: Implement proper version history in the Prompt Registry (currently always `1.0.0`)

---

*End of MEDAgent Engineering Reference Book — Version 5.3.0*
