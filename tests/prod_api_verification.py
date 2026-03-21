import asyncio
import os
import sys
import unittest

from fastapi.testclient import TestClient

# Add project root to sys.path
sys.path.append("d:\\MedAgent")

from api.main import app
from config import settings


class TestMedAgentAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.admin_headers = {"X-Admin-Key": settings.ADMIN_API_KEY}

    def test_health(self):
        """Test system health and readiness."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

        response = self.client.get("/ready")
        # Might be 503 if agents not fully ready, but should return valid JSON
        self.assertIn(response.status_code, [200, 503])

    def test_metrics(self):
        """Test prometheus metrics endpoint."""
        response = self.client.get("/metrics")
        self.assertEqual(response.status_code, 200)
        self.assertIn("medagent_", response.text)

    def test_auth_failure(self):
        """Test authentication enforcement."""
        # /auth/me requires JWT
        response = self.client.get("/auth/me")
        self.assertEqual(response.status_code, 401)

        # /admin/review-action requires Admin Key
        response = self.client.post("/admin/review-action", json={})
        self.assertEqual(response.status_code, 403)

    def test_consultation_flow(self):
        """Test the primary consultation endpoint (mocked agents if possible or real)."""
        # We'll use a simple symptom that should pass triage
        payload = {
            "symptoms": "I have a slight headache and feel tired.",
            "patient_id": "test_patient_001",
        }
        # This will trigger the actual LangGraph if API keys are present.
        # If keys are missing, it might return 500 or 400.
        # We just want to check if the route is wired correctly.
        response = self.client.post("/consult", json=payload)
        self.assertIn(response.status_code, [200, 400, 500])


if __name__ == "__main__":
    unittest.main()
