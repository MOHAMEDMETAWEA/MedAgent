from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from api.deps import (check_admin_auth, get_current_user, get_export_agent,
                      get_governance, get_persistence)
from database.models import AIAuditLog, Interaction, UserSession

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


@router.get("/overview")
async def get_analytics_overview(admin: dict = Depends(check_admin_auth)):
    """Retrieve global system health and clinical performance metrics (Admin only)."""
    pers = get_persistence()
    db = pers.db
    try:
        from sqlalchemy import func

        from learning.feedback_loop import FeedbackRLLoop

        rl_loop = FeedbackRLLoop()
        learning_stats = rl_loop.analyze_clinical_trends()

        total_sessions = db.query(UserSession).count()
        total_interactions = db.query(Interaction).count()

        # Risk distribution
        high_risk_count = (
            db.query(Interaction).filter(Interaction.risk_level == "High").count()
        )
        emergency_count = (
            db.query(Interaction).filter(Interaction.risk_level == "Emergency").count()
        )

        # Safety Blocks

        safety_alerts = learning_stats.get("safety_alerts", 0)

        # Latency (Avg)
        avg_latency_raw = db.query(func.avg(Interaction.latency_ms)).scalar()
        avg_latency = float(avg_latency_raw) if avg_latency_raw is not None else 0.0

        # Agent Performance (Mocked for now)
        agent_perf = {
            "TriageAgent": 0.92,
            "ReasoningAgent": 0.88,
            "VisionAgent": 0.85,
            "ValidationAgent": 0.98,
        }

        return {
            "total_interactions": total_interactions,
            "total_sessions": total_sessions,
            "safety_alerts": safety_alerts,
            "avg_latency": round(avg_latency / 1000.0, 2),  # Convert ms to s
            "weighted_score": float(learning_stats.get("system_weighted_score", 0.0)),
            "risk_distribution": {
                "Emergency": emergency_count,
                "High": high_risk_count,
                "Stable": total_interactions - high_risk_count - emergency_count,
            },
            "agent_performance": agent_perf,
            "feedback_stats": learning_stats,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Metrics aggregation failed: {str(e)}"
        )
