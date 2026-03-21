from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from api.deps import (get_current_user, get_export_agent, get_governance,
                      get_persistence)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


class SymptomRequest(BaseModel):
    symptom: str
    severity: int
    notes: Optional[str] = None


class MedicationRequest(BaseModel):
    name: str
    dosage: str
    frequency: str


@router.post("/symptoms")
async def log_symptom(req: SymptomRequest, user: dict = Depends(get_current_user)):
    pers = get_persistence()
    success = await pers.log_symptom(user["sub"], req.symptom, req.severity, req.notes)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to log symptom")
    return {"status": "success"}


@router.get("/symptoms")
async def get_symptoms(user: dict = Depends(get_current_user)):
    pers = get_persistence()
    return await pers.get_symptoms(user["sub"])


@router.post("/medications")
async def log_medication(
    req: MedicationRequest, user: dict = Depends(get_current_user)
):
    pers = get_persistence()
    success = await pers.log_medication(
        user["sub"], req.name, req.dosage, req.frequency
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to log medication")
    return {"status": "success"}


@router.get("/medications")
async def get_medications(user: dict = Depends(get_current_user)):
    pers = get_persistence()
    return await pers.get_medications(user["sub"])


@router.get("/export-pdf")
async def export_analytics_report(user: dict = Depends(get_current_user)):
    pers = get_persistence()
    exporter = get_export_agent()
    gov = get_governance()

    # Fetch patient profile
    # Using PersistenceAgent internal db access for complex query
    db = pers.db
    try:
        from database.models import Interaction, PatientProfile, UserSession

        p = db.query(PatientProfile).filter(PatientProfile.id == user["sub"]).first()
        if not p:
            raise HTTPException(status_code=404, detail="Profile not found")

        profile_dict = {"id": p.id, "age": p.age, "gender": p.gender}

        # Fetch last 20 interactions
        items = (
            db.query(Interaction)
            .filter(
                Interaction.session_id.in_(
                    db.query(UserSession.id).filter(UserSession.user_id == user["sub"])
                )
            )
            .order_by(Interaction.timestamp.desc())
            .limit(20)
            .all()
        )

        interactions = []
        for i in items:
            interactions.append(
                {
                    "timestamp": i.timestamp.isoformat(),
                    "diagnosis": gov.decrypt(i.diagnosis_output_encrypted),
                    "audit_hash": i.audit_hash,
                }
            )

        file_path = f"export_{user['sub']}.pdf"
        success = exporter.generate_patient_summary_pdf(
            profile_dict, interactions, file_path
        )

        if success:
            return FileResponse(
                file_path, media_type="application/pdf", filename="MedAgent_Report.pdf"
            )
        else:
            raise HTTPException(status_code=500, detail="PDF generation failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
