"""
Basic system tests for MedAgent.
Run from project root: python -m pytest evaluation/test_system.py -v
Or: python evaluation/test_system.py
"""
import sys
from pathlib import Path

# Ensure project root is on path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))


def test_imports():
    """Verify core modules can be imported."""
    from config import settings
    assert settings.BASE_DIR is not None
    from utils.safety import validate_medical_input, sanitize_input
    assert validate_medical_input("I have a headache")[0] is True
    from utils.rate_limit import check_rate_limit
    allowed, _ = check_rate_limit("127.0.0.1")
    assert allowed is True
    from agents.state import AgentState
    assert "messages" in AgentState.__annotations__


def test_health_endpoint():
    """Verify / and /health return 200."""
    from fastapi.testclient import TestClient
    from api.main import app
    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 200
    assert "version" in r.json()
    r2 = client.get("/health")
    assert r2.status_code == 200
    assert r2.json().get("status") == "ok"


def test_ready_without_api_key():
    """Without OPENAI_API_KEY, /ready should return 503."""
    from fastapi.testclient import TestClient
    from api.main import app
    client = TestClient(app)
    r = client.get("/ready")
    # 503 when orchestrator cannot be created (e.g. missing API key)
    assert r.status_code in (503, 200)
    assert "version" in r.json()


def test_consult_validation():
    """Invalid input to /consult should return 422."""
    from fastapi.testclient import TestClient
    from api.main import app
    client = TestClient(app)
    r = client.post("/consult", json={"symptoms": ""})
    assert r.status_code == 422  # Pydantic validation error for empty string


def test_agent_response_schema():
    """AgentResponse model includes all fields (summary, diagnosis, report fields, etc.)."""
    from api.main import AgentResponse
    schema = AgentResponse.model_json_schema()
    props = schema.get("properties", {})
    assert "summary" in props
    assert "diagnosis" in props
    assert "appointment" in props
    assert "doctor_review" in props
    assert "is_emergency" in props
    assert "medical_report" in props
    assert "doctor_summary" in props
    assert "patient_instructions" in props


def test_report_agent_import():
    """Report agent and state report fields are available."""
    from agents.state import AgentState
    from agents.report_agent import ReportAgent
    assert "report_medical" in AgentState.__annotations__
    assert "report_doctor_summary" in AgentState.__annotations__
    assert "report_patient_instructions" in AgentState.__annotations__
    assert hasattr(ReportAgent, "process")
    assert callable(getattr(ReportAgent, "process", None))


if __name__ == "__main__":
    test_imports()
    print("test_imports OK")
    test_health_endpoint()
    print("test_health_endpoint OK")
    test_ready_without_api_key()
    print("test_ready_without_api_key OK")
    test_consult_validation()
    print("test_consult_validation OK")
    test_agent_response_schema()
    print("test_agent_response_schema OK")
    test_report_agent_import()
    print("test_report_agent_import OK")
    print("All tests passed.")
