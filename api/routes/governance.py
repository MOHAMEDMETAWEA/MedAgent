"""
Clinical Governance & HITL Review Routes.
"""
from fastapi import APIRouter, HTTPException, Depends
from database.models import AIAuditLog, SessionLocal, Interaction, ReviewStatus

router = APIRouter(prefix="/governance", tags=["Governance"])

@router.get("/audit-logs")
async def get_audit_logs(limit: int = 50):
    with SessionLocal() as db:
        return db.query(AIAuditLog).order_by(AIAuditLog.timestamp.desc()).limit(limit).all()

@router.post("/review/approve")
async def approve_case(interaction_id: int, comment: str):
    with SessionLocal() as db:
        interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
        if not interaction:
            raise HTTPException(status_code=404, detail="Interaction not found")
        interaction.review_status = ReviewStatus.APPROVED
        interaction.reviewer_comment = comment
        db.commit()
        return {"status": "Case approved"}
