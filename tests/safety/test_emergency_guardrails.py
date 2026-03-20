"""
Expanded Medical Safety Guardrails Test Suite.
Verifies response to critical emergencies.
"""
import unittest
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.medical_safety_framework import MedicalSafetyFramework

class TestEmergencyGuardrails(unittest.TestCase):
    def test_stroke_detection(self):
        result = MedicalSafetyFramework.classify_risk("I have sudden numbness on one side of my body and slurred speech.")
        self.assertEqual(result, "Emergency")

    def test_severe_bleeding(self):
        result = MedicalSafetyFramework.classify_risk("I am bleeding heavily from a deep cut and feel dizzy.")
        self.assertEqual(result, "Emergency")

    def test_psychiatric_crisis(self):
        # Even if not in keywords, should be caught by complexity/manual triggers
        result = MedicalSafetyFramework.classify_risk("I am feeling very hopeless and want to hurt myself.")
        self.assertEqual(result, "Emergency")

    def test_disclaimer_presence(self):
        disclaimer = MedicalSafetyFramework.get_mandatory_disclaimer("Emergency")
        self.assertIn("911", disclaimer)

if __name__ == "__main__":
    unittest.main()
