"""
Integration tests for HL7 FHIR Interoperability.
"""
import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import asyncio

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from integrations.fhir_connector import FHIRConnector

class TestFHIRIntegration(unittest.TestCase):
    
    @patch('httpx.AsyncClient.get')
    def test_get_patient_fhir(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"resourceType": "Patient", "id": "123", "name": [{"family": "Doe"}]}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        connector = FHIRConnector(base_url="https://mock-fhir.com")
        loop = asyncio.get_event_loop()
        patient = loop.run_until_complete(connector.get_patient("123"))
        
        self.assertEqual(patient['resourceType'], "Patient")
        mock_get.assert_called_once()
        print("FHIR Patient retrieval verified.")

    @patch('httpx.AsyncClient.get')
    def test_get_conditions_fhir(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"resourceType": "Bundle", "entry": [{"resource": {"resourceType": "Condition", "code": {"text": "Hypertension"}}}]}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        connector = FHIRConnector(base_url="https://mock-fhir.com")
        loop = asyncio.get_event_loop()
        conditions = loop.run_until_complete(connector.get_conditions("123"))
        
        self.assertTrue(len(conditions) > 0)
        print("FHIR Conditions retrieval verified.")

if __name__ == '__main__':
    unittest.main()
