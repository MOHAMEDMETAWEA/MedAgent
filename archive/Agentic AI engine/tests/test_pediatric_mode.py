"""
Unit tests for the Pediatric Agent (Theo).
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.pediatric_agent import PediatricAgent


class TestPediatricAgent(unittest.TestCase):

    def setUp(self):
        self.agent = PediatricAgent()

    @patch("models.model_router.get_model")
    def test_pediatric_explanation(self, mock_get_model):
        from langchain_core.runnables import RunnableLambda

        async def mock_call(*args, **kwargs):
            return MagicMock(
                content="Theo says: Your body has a tiny army of soldiers fighting the bad bugs!"
            )

        mock_llm = RunnableLambda(mock_call)
        mock_get_model.return_value = mock_llm

        # Refresh the agent's LLM since it's initialized in __init__
        self.agent.llm = mock_llm

        import asyncio

        result = asyncio.run(
            self.agent.process(
                {
                    "preliminary_diagnosis": "Patient has acute influenza with high viral load",
                    "user_age": 6,
                }
            )
        )

        self.assertIn("Theo", result["theo_explanation"])
        self.assertIn("soldier", result["theo_explanation"].lower())
        self.assertIn("visual_description", result)
        print("Pediatric Theory verified.")


if __name__ == "__main__":
    unittest.main()
