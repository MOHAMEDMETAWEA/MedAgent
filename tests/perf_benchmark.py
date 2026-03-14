import sys
import os
import time
import unittest
from fastapi.testclient import TestClient

# Add project root to sys.path
sys.path.append('d:\\MedAgent')

import tests.ai_mocks
from api.main import app

class TestMedAgentPerformance(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_latency_consultation(self):
        """Measure latency of a standard consultation with mocks."""
        start_time = time.time()
        payload = {
            "symptoms": "Mild headache and fatigue.",
            "patient_id": "perf_test_user"
        }
        response = self.client.post("/consult", json=payload)
        latency = time.time() - start_time
        
        self.assertEqual(response.status_code, 200)
        print(f"Consultation Latency (Mocked): {latency:.4f}s")
        self.assertLess(latency, 5.0, "Latency too high even for mocks!")

    def test_latency_health_check(self):
        """Health check should be near-instant."""
        start_time = time.time()
        response = self.client.get("/health")
        latency = time.time() - start_time
        self.assertEqual(response.status_code, 200)
        print(f"Health Check Latency: {latency:.4f}s")

if __name__ == "__main__":
    unittest.main()
