"""
Clinical Governance & HITL Review Routes.
"""

from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_current_user, oauth2_scheme
from database.models import AIAuditLog, Interaction, ReviewStatus, SessionLocal

router = APIRouter(prefix="/governance", tags=["Governance"])


@router.get("/audit-logs")
async def get_audit_logs(limit: int = 50, token: str = Depends(oauth2_scheme)):
    """Retrieve high-fidelity AI audit logs for clinical compliance."""
    with SessionLocal() as db:
        return (
            db.query(AIAuditLog)
            .order_by(AIAuditLog.timestamp.desc())
            .limit(limit)
            .all()
        )


@router.post("/review/approve")
async def approve_case(
    interaction_id: int, comment: str, token: str = Depends(oauth2_scheme)
):
    """Doctor approval for a high-risk AI suggestion."""
    with SessionLocal() as db:
        interaction = (
            db.query(Interaction).filter(Interaction.id == interaction_id).first()
        )
        if interaction:
            interaction.review_status = ReviewStatus.APPROVED
            interaction.reviewer_comment = comment
            db.commit()
            return {"status": "Case approved"}
        raise HTTPException(status_code=404, detail="Interaction not found")


@router.get("/compliance/export")
async def export_compliance_report(
    format: str = "fhir", token: str = Depends(oauth2_scheme)
):
    """Export clinical logs in regulated formats (FHIR AuditEvent)."""
    from utils.audit_logger import AuditLogger

    if format == "fhir":
        return AuditLogger.export_fhir_audit_event(
            log_id=0
        )  # Placeholder for batch export
    return {"error": "Unsupported format"}
