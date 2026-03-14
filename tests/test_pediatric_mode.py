"""
Unit tests for the Pediatric Agent (Theo).
"""
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.pediatric_agent import PediatricAgent

class TestPediatricAgent(unittest.TestCase):
    
    def setUp(self):
        self.agent = PediatricAgent()

    @patch('models.model_router.get_model')
    def test_pediatric_explanation(self, mock_get_model):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="Theo says: Your body has a tiny army of soldiers fighting the bad bugs!")
        mock_get_model.return_value = mock_llm
        
        # Refresh the agent's LLM since it's initialized in __init__
        self.agent.llm = mock_llm
        
        result = self.agent.process_explanation("Patient has acute influenza with high viral load", age=6)
        
        self.assertIn("Theo", result["theo_explanation"])
        self.assertIn("soldier", result["theo_explanation"].lower())
        self.assertIn("visual_description", result)
        print("Pediatric Theory verified.")

if __name__ == '__main__':
    unittest.main()
