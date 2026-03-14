"""
Unit tests for Local Model Routing.
"""
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import settings
from models.model_router import get_model

class TestLocalModelRouting(unittest.TestCase):
    
    @patch('models.model_router.ChatOpenAI')
    def test_cloud_routing(self, mock_openai):
        settings.MODEL_MODE = "cloud"
        get_model(model_name="gpt-4o")
        mock_openai.assert_called_once()
        print("Cloud routing verified.")

    @patch('models.model_router.ChatOllama')
    def test_local_ollama_routing(self, mock_ollama):
        settings.MODEL_MODE = "local"
        # Simulate ollama being requested or implicit
        with patch('models.model_router.settings') as mock_settings:
            mock_settings.MODEL_MODE = "local"
            mock_settings.OLLAMA_URL = "http://localhost:11434"
            get_model(model_name="meditron", provider="ollama")
            mock_ollama.assert_called_once()
        print("Local Ollama routing verified.")

    @patch('models.model_router.ChatOpenAI')
    def test_local_vllm_routing(self, mock_vllm):
        settings.MODEL_MODE = "local"
        with patch('models.model_router.settings') as mock_settings:
            mock_settings.MODEL_MODE = "local"
            mock_settings.OLLAMA_URL = ""
            mock_settings.VLLM_URL = "http://localhost:8000/v1"
            get_model(model_name="mistral")
            # vLLM uses ChatOpenAI with custom base_url
            mock_vllm.assert_called_once()
            args, kwargs = mock_vllm.call_args
            self.assertEqual(kwargs['openai_api_base'], "http://localhost:8000/v1")
        print("Local vLLM routing verified.")

if __name__ == '__main__':
    unittest.main()
