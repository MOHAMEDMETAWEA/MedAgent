import sys
import os
import unittest
import json
from fastapi.testclient import TestClient

# Add project root to sys.path
sys.path.append('d:\\MedAgent')

import tests.ai_mocks
from api.main import app

class TestMedAgentVision(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.image_path = "d:\\MedAgent\\test_Xray.jpeg"

    def test_vision_consultation(self):
        """Test sending symptoms with an image."""
        if not os.path.exists(self.image_path):
            self.skipTest(f"Image not found at {self.image_path}")
            
        payload = {
            "symptoms": "I have pain in my chest. Looking at this X-ray.",
            "patient_id": "vision_test_user",
            "image_path": self.image_path
        }
        
        response = self.client.post("/consult", json=payload)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        self.assertIn("final_response", result)
        # Check if vision agent was likely triggered (visual_findings exists in result or status)
        self.assertTrue("visual_findings" in result)
        print("Vision Response Summary:", result.get("final_response")[:100] + "...")

if __name__ == "__main__":
    unittest.main()
