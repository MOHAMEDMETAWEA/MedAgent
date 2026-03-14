"""
HL7 FHIR R4 Connector - Interoperability layer for EMR integration.
Supports Epic, Cerner, and standard FHIR servers.
"""
import logging
import httpx
from typing import Optional, Dict, List
from config import settings

logger = logging.getLogger(__name__)

class FHIRConnector:
    def __init__(self, base_url: str, auth_token: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Accept": "application/fhir+json",
            "Content-Type": "application/fhir+json"
        }
        if auth_token:
            self.headers["Authorization"] = f"Bearer {auth_token}"

    async def get_patient(self, patient_id: str) -> Dict:
        """Fetch patient demographics."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/Patient/{patient_id}", headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def get_conditions(self, patient_id: str) -> List[Dict]:
        """Fetch clinical conditions."""
        async with httpx.AsyncClient() as client:
            params = {"patient": patient_id}
            response = await client.get(f"{self.base_url}/Condition", headers=self.headers, params=params)
            response.raise_for_status()
            bundle = response.json()
            return bundle.get("entry", [])

    async def get_medications(self, patient_id: str) -> List[Dict]:
        """Fetch active medication requests."""
        async with httpx.AsyncClient() as client:
            params = {"patient": patient_id}
            response = await client.get(f"{self.base_url}/MedicationRequest", headers=self.headers, params=params)
            response.raise_for_status()
            bundle = response.json()
            return bundle.get("entry", [])

    async def get_observations(self, patient_id: str, category: str = "vital-signs") -> List[Dict]:
        """Fetch clinical observations (vitals, labs)."""
        async with httpx.AsyncClient() as client:
            params = {"patient": patient_id, "category": category}
            response = await client.get(f"{self.base_url}/Observation", headers=self.headers, params=params)
            response.raise_for_status()
            bundle = response.json()
            return bundle.get("entry", [])

    async def push_diagnostic_report(self, report_data: Dict) -> Dict:
        """Send diagnostic report back to EMR."""
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/DiagnosticReport", headers=self.headers, json=report_data)
            response.raise_for_status()
            return response.json()
