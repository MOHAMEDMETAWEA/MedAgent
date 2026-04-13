import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class FHIRPatient(BaseModel):
    id: str
    active: bool = True
    name: List[Dict[str, Any]]
    gender: str
    birthDate: str
    telecom: List[Dict[str, Any]] = []


class FHIRObservation(BaseModel):
    id: Optional[str]
    status: str = "final"
    category: List[Dict[str, Any]]
    code: Dict[str, Any]  # LOINC code
    subject: Dict[str, Any]  # Reference to Patient
    effectiveDateTime: str
    valueQuantity: Optional[Dict[str, Any]] = None


class EHRIntegrationManager:
    """
    Phase 2: EHR Interoperability (FHIR R4 / HL7)
    Responsibilities:
    - Sync patient data from external EHRs.
    - Export AI-DiagnosticReports to EHRs.
    - Transform internal schemas to FHIR-compliant JSON.
    """

    def __init__(self):
        self.ehr_endpoint = "https://mock-hospital-ehr.org/api/fhir/v4"

    async def sync_patient_record(self, patient_id: str) -> Dict[str, Any]:
        """Fetch full patient record from EHR (Simulated)."""
        logger.info(f"EHR: Syncing patient {patient_id} from external EHR...")
        # Simulated FHIR Response
        return {
            "resourceType": "Bundle",
            "id": f"bundle-{patient_id}",
            "type": "collection",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "id": patient_id,
                        "name": [{"family": "Doe", "given": ["John"]}],
                    }
                },
                {
                    "resource": {
                        "resourceType": "Observation",
                        "code": {
                            "coding": [{"system": "http://loinc.org", "code": "8867-4"}]
                        },
                        "valueQuantity": {"value": 72, "unit": "bpm"},
                    }
                },
            ],
        }

    async def upload_diagnostic_report(
        self, interaction_id: int, ai_diagnosis: str
    ) -> bool:
        """Export an AI-generated report as a FHIR DiagnosticReport."""
        report = {
            "resourceType": "DiagnosticReport",
            "status": "final",
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                            "code": "GE",
                        }
                    ]
                }
            ],
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "602-2",
                        "display": "AI Diagnostic Analysis",
                    }
                ]
            },
            "subject": {"reference": "Patient/example"},
            "issued": datetime.utcnow().isoformat(),
            "conclusion": ai_diagnosis,
            "presentedForm": [],
        }
        logger.info(
            f"EHR: Uploaded AI DiagnosticReport for interaction {interaction_id}"
        )
        return True

    def map_to_fhir_condition(self, diagnosis: str, severity: str) -> Dict[str, Any]:
        """Convert internal diagnosis to FHIR Condition resource."""
        return {
            "resourceType": "Condition",
            "clinicalStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                        "code": "active",
                    }
                ]
            },
            "verificationStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                        "code": "provisional",
                    }
                ]
            },
            "code": {"text": diagnosis},
            "severity": {"text": severity},
            "subject": {"reference": "Patient/example"},
            "recordedDate": datetime.utcnow().isoformat(),
        }


# Singleton Instance
ehr_manager = EHRIntegrationManager()
