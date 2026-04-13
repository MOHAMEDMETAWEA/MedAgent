import json
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from api.deps import (get_current_user, get_governance, get_interop_builder,
                      get_persistence)
from integrations.ehr_integration import ehr_manager

router = APIRouter(prefix="/ehr", tags=["EHR Integration"])


class InteropRequest(BaseModel):
    report_id: int


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


@router.post("/interop/fhir")
async def export_fhir(req: InteropRequest, user: dict = Depends(get_current_user)):
    pers = get_persistence()
    gov = get_governance()
    from database.models import MedicalReport

    # Fetch report and related interaction/session
    report = (
        pers.db.query(MedicalReport)
        .filter(
            MedicalReport.id == req.report_id, MedicalReport.patient_id == user["sub"]
        )
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    # Build clinical data from decrypted report content and minimal metadata
    content = json.loads(gov.decrypt(report.report_content_encrypted))
    clinical_data = {
        "patient_id": report.patient_id,
        "generated_at": str(report.generated_at),
        "language": report.language,
        "report": content,
    }
    builder = get_interop_builder()
    fhir = builder.build_fhir_bundle(clinical_data)
    if isinstance(fhir, dict) and fhir.get("error"):
        raise HTTPException(status_code=500, detail=fhir["error"])
    return JSONResponse(content=fhir)


@router.post("/interop/hl7")
async def export_hl7(req: InteropRequest, user: dict = Depends(get_current_user)):
    pers = get_persistence()
    gov = get_governance()
    from database.models import MedicalReport

    report = (
        pers.db.query(MedicalReport)
        .filter(
            MedicalReport.id == req.report_id, MedicalReport.patient_id == user["sub"]
        )
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    content = json.loads(gov.decrypt(report.report_content_encrypted))
    interaction_data = {
        "patient_id": report.patient_id,
        "generated_at": str(report.generated_at),
        "language": report.language,
        "report": content,
    }
    builder = get_interop_builder()
    hl7 = builder.build_hl7_v2(interaction_data)
    if isinstance(hl7, str) and hl7.startswith("ERROR:"):
        raise HTTPException(status_code=500, detail=hl7)
    return JSONResponse(content={"hl7": hl7})
