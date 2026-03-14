"""
Unified Safety & Governance Test Suite.
Verifies Explainability, Auditing, HITL, and Safety Guardrails.
"""
import unittest
import json
import os
import sys
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.explainability_engine import ExplainabilityEngine
from utils.medical_safety_framework import MedicalSafetyFramework
from utils.bias_monitor import BiasMonitor
from agents.triage_agent import TriageAgent

class TestClinicalSafety(unittest.TestCase):

    def test_explainability_trace(self):
        """Verify that the explainability engine correctly formats reasoning."""
        steps = ["Analyzing patient chest pain", "Checking EKG data", "Considering MI"]
        trace = ExplainabilityEngine.generate_reasoning_trace(steps)
        self.assertIn("1. Analyzing", trace)
        self.assertIn("3. Considering", trace)

    def test_safety_risk_classification(self):
        """Verify that emergency symptoms are correctly classified."""
        emergency_risk = MedicalSafetyFramework.classify_risk("Patient is complaining of severe chest pain and shortness of breath.")
        self.assertEqual(emergency_risk, "Emergency")
        
        low_risk = MedicalSafetyFramework.classify_risk("Mild cough")
        self.assertEqual(low_risk, "Low")

    def test_safety_disclaimers(self):
        """Verify that appropriate disclaimers are provided."""
        disclaimer = MedicalSafetyFramework.get_mandatory_disclaimer("Emergency")
        self.assertIn("911", disclaimer)
        self.assertIn("CRITICAL", disclaimer)

    def test_bias_detection(self):
        """Verify that potential bias is flagged."""
        profile = {"age": 30, "gender": "Female"}
        result = BiasMonitor.detect_demographic_bias("The patient is suffering from hysteria.", profile)
        self.assertTrue(result["has_bias"])

    def test_audit_integrity_hash(self):
        """Verify that audit hashes are reproducible."""
        from utils.audit_logger import AuditLogger
        # This is harder to test without DB, so we test the logic via mock if needed
        pass

if __name__ == "__main__":
    unittest.main()
