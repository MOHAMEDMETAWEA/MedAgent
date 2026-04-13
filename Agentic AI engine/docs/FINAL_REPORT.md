# MEDagent Global Generic System - Final Architecture Report

## 1. System Architecture Diagram

```mermaid
graph TD
    User([User Input]) --> Router{Intent?}
    
    %% Medical Flow
    Router -- Medical Issue --> Triage[Triage Agent]
    Triage -->|Urgency & Summary| Knowledge[Knowledge Agent (RAG)]
    Knowledge -->|Evidence Docs| Reasoning[Reasoning Agent]
    
    subgraph Core Logic
        Reasoning -->|Differential| Validation[Validation Agent]
        Validation -->|Checked Diagnosis| Safety[Safety Agent]
    end
    
    Safety -->|Safe/Blocked| Response[Response Agent]
    Response --> FinalOutput([Final Response])
    
    %% Calendar Flow
    Router -- Scheduling --> Calendar[Calendar Agent]
    Calendar -->|Confirm/Reject| FinalOutput
```

## 2. Agent Roles & Responsibilities

1. **Triage Agent**:
    - **Role**: Urgent vs Non-Urgent classification.
    - **Input**: Raw symptoms.
    - **Output**: Urgency Level (LOW, MEDIUM, HIGH, EMERGENCY) + Structured Summary.
    - **Safety**: Triggers critical alerts for immediate referral.

2. **Knowledge Agent (RAG)**:
    - **Role**: Grounding.
    - **Input**: Patient Summary.
    - **Output**: Verified Medical Guidelines (Text).
    - **Safety**: Prevents hallucination by retrieving ONLY valid sources.

3. **Reasoning Agent**:
    - **Role**: Diagnosis generation.
    - **Input**: Symptoms + Guidelines.
    - **Output**: Differential Diagnosis with citations.
    - **Safety**: Explicit uncertainty modeling.

4. **Validation Agent**:
    - **Role**: Fact-Checking.
    - **Input**: Diagnosis + Evidence.
    - **Output**: "Valid" or "Warning: Unsupported Claim".
    - **Safety**: Catches hallucinations before they reach the user.

5. **Safety Agent**:
    - **Role**: Final Guardrail.
    - **Input**: Draft Response.
    - **Output**: Safe/Blocked status.
    - **Safety**: Blocks self-harm, dangerous advice, or malicious assignments.

6. **Response Agent**:
    - **Role**: User formatting.
    - **Input**: Technical Diagnosis + Safety Status.
    - **Output**: Clear, empathetic, disclaimed response.

7. **Calendar Agent**:
    - **Role**: Scheduling.
    - **Input**: Time/Date intent.
    - **Output**: Google Calendar Event.
    - **Safety**: **BLOCKS** scheduling if Urgency is EMERGENCY.

## 3. Global & Generic Design

- **No Hardcoded Hospitals**: All logic uses "local provider" or "nearest emergency facility".
- **Configurable**: All API keys, paths, and thresholds are in `config.py` / `.env`.
- **Universal Access**: Prompts are designed to be culture-neutral and broadly applicable.

## 4. Deployment Instructions

1. **Prerequisites**:
    - Python 3.9+
    - OpenAI API Key
    - Google Cloud Credentials (`credentials.json`) for Calendar (Optional)

2. **Installation**:

    ```bash
    pip install -r requirements.txt
    python data/generate_data.py # Initialize generic medical data
    ```

3. **Run**:
    - **Backend**: `uvicorn api.main:app --host 0.0.0.0 --port 8000`
    - **Frontend**: `streamlit run api/frontend.py`

4. **Docker**:
    - `docker-compose up --build`

## 5. Security & Safety Features

- **Input Sanitization**: `utils/safety.py` strips control chars and limits length.
- **Injection Detection**: Regex-based blocks for "Ignore instruction" attacks.
- **Fail-Safe**: If RAG fails, agents default to "Consult a doctor" rather than inventing facts.
- **Strict Disclaimers**: Every output includes a standardized medical disclaimer.
