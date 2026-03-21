from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_current_user
from integrations.ehr_integration import ehr_manager

router = APIRouter(prefix="/ehr", tags=["EHR Integration"])


@router.post("/sync/{patient_id}")
async def sync_ehr_data(patient_id: str, current_user: Any = Depends(get_current_user)):
    """Synchronize MEDAgent memory with external Hospital EHR (FHIR)."""
    try:
        data = await ehr_manager.sync_patient_record(patient_id)
        return {
            "status": "success",
            "patient_id": patient_id,
            "data_synced": True,
            "fhir_bundle": data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"EHR Sync Failed: {str(e)}")


@router.get("/patient/{patient_id}")
async def get_patient_ehr(
    patient_id: str, current_user: Any = Depends(get_current_user)
):
    """Retrieve external EHR data for a specific patient."""
    data = await ehr_manager.sync_patient_record(patient_id)
    return data


@router.post("/report")
async def push_ai_report(
    interaction_id: int, diagnosis: str, current_user: Any = Depends(get_current_user)
):
    """Push AI DiagnosticReport to hospital systems."""
    success = await ehr_manager.upload_diagnostic_report(interaction_id, diagnosis)
    return {"status": "success" if success else "failed"}
