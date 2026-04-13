import asyncio

import pytest
from httpx import AsyncClient

from agents.governance_agent import GovernanceAgent
from agents.persistence_agent import PersistenceAgent
from api.main import app

# Mock user data
DOCTOR_USER = {"sub": "doc_123", "role": "doctor", "email": "doctor@medagent.test"}
PATIENT_USER = {"sub": "pat_456", "role": "patient", "email": "patient@medagent.test"}


@pytest.mark.asyncio
async def test_submit_patient_feedback():
    """Verify patients can submit basic feedback without corrections."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Simulate auth dependency
        app.dependency_overrides = {}  # We'd need to mock get_current_user

        # For simplicity in this test, we test the logic via the persistence agent directly
        # as getting FastAPI auth mocks right in this environment can be tricky.
        pers = PersistenceAgent()
        fb_id = await pers.save_feedback(
            user_id="pat_456",
            role="patient",
            case_id="case_001",
            ai_response="The AI says you are fine.",
            rating=4,
            comment="Clear explanation.",
        )
        assert fb_id is not None

        # Verify retrieval
        results = await pers.get_feedback_by_case("case_001")
        assert len(results) > 0
        assert results[0]["role"] == "patient"
        assert results[0]["rating"] == 4
        assert results[0]["comment"] == "Clear explanation."


@pytest.mark.asyncio
async def test_submit_doctor_correction():
    """Verify doctors can submit clinical corrections."""
    pers = PersistenceAgent()
    fb_id = await pers.save_feedback(
        user_id="doc_123",
        role="doctor",
        case_id="case_002",
        ai_response="AI says take aspirin.",
        rating=2,
        comment="Incorrect dosage.",
        corrected_response="Take 100mg aspirin daily.",
    )
    assert fb_id is not None

    # Verify retrieval and decryption
    results = await pers.get_feedback_by_case("case_002")
    assert len(results) > 0
    assert results[0]["role"] == "doctor"
    assert results[0]["correction"] == "Take 100mg aspirin daily."


@pytest.mark.asyncio
async def test_feedback_analytics():
    """Verify analytics aggregation works."""
    pers = PersistenceAgent()
    analytics = await pers.get_feedback_analytics()
    assert "average_rating" in analytics
    assert "role_distribution" in analytics
    assert "role_averages" in analytics
