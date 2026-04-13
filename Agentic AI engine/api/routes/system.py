"""
System Health, Metrics, and Admin Controls.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel

from api.deps import (check_admin_auth, get_audit_agent, get_current_user,
                      get_developer_agent, get_governance, get_improver,
                      get_persistence, get_review_agent)

router = APIRouter(prefix="/system", tags=["System"])


class UserActionRequest(BaseModel):
    session_id: str
    action_type: str
    element_id: str
    details: Optional[dict] = None


class AdminReviewAction(BaseModel):
    interaction_id: int
    action: str  # APPROVE or REJECT
    comment: Optional[str] = None


class ABTestRequest(BaseModel):
    prompt_id: str
    prompt_a: str
    prompt_b: str
    test_cases: list


class RegistryReviewRequest(BaseModel):
    old_hash: str
    new_hash: str
    delta_report: str


class OverrideEscalationRequest(BaseModel):
    interaction_id: int
    override: bool
    rationale: Optional[str] = None


class AuditExportRequest(BaseModel):
    interaction_id: Optional[int] = None


@router.get("/health")
async def health():
    return {"status": "ok", "version": "5.3.0"}


@router.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@router.post("/log-action")
async def log_action(request: UserActionRequest):
    """Log a granular user UI action."""
    pers = get_persistence()
    success = await pers.save_user_action(
        session_id=request.session_id,
        action_type=request.action_type,
        element_id=request.element_id,
        details=request.details or {},
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to log action")
    return {"status": "logged"}


@router.get("/admin/health", dependencies=[Depends(check_admin_auth)])
async def admin_health():
    agent = get_developer_agent()
    return agent.get_system_health()


@router.get("/audit-logs", dependencies=[Depends(check_admin_auth)])
async def get_audit_logs(limit: int = 100):
    """Retrieve system audit logs (Admin API Key auth)."""
    audit = get_audit_agent()
    return audit.get_logs(limit=limit)


@router.get("/audit-trail")
async def get_audit_trail(limit: int = 100, user: dict = Depends(get_current_user)):
    """Retrieve audit logs for doctor/admin users via JWT auth.
    This is the endpoint the frontend Audit tab uses."""
    role = user.get("role", "")
    if role not in ["admin", "doctor"]:
        raise HTTPException(status_code=403, detail="Admin/Doctor clearance required")
    audit = get_audit_agent()
    return audit.get_logs(limit=limit)


@router.post("/register-dev", dependencies=[Depends(check_admin_auth)])
async def register_dev(username: str):
    """Register a new developer (simulated)."""
    developer_agent = get_developer_agent()
    return developer_agent.register_developer(username=username)


@router.get("/test", dependencies=[Depends(check_admin_auth)])
async def trigger_tests():
    """Run full system test suite."""
    developer_agent = get_developer_agent()
    return developer_agent.trigger_system_test()


@router.get("/admin/pending-reviews", dependencies=[Depends(check_admin_auth)])
async def get_pending_reviews():
    """Get interactions flagged for human review."""
    review_agent = get_review_agent()
    gov = get_governance()
    items = review_agent.get_flagged_interactions()

    results = []
    for i in items:
        results.append(
            {
                "id": i.id,
                "session_id": i.session_id,
                "user_input": gov.decrypt(i.user_input_encrypted),
                "diagnosis": gov.decrypt(i.diagnosis_output_encrypted),
                "timestamp": i.timestamp,
            }
        )
    return results


@router.post("/admin/review-action", dependencies=[Depends(check_admin_auth)])
async def review_action(action: AdminReviewAction):
    """Approve or Reject a flagged response."""
    review_agent = get_review_agent()
    success = review_agent.process_review_action(
        interaction_id=action.interaction_id,
        status=action.action,
        comment=action.comment,
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to process review action")
    return {"status": "updated", "action": action.action}


@router.get("/admin/improvement-report", dependencies=[Depends(check_admin_auth)])
async def improvement_report():
    """Get Self-Improvement analysis."""
    improver = get_improver()
    report = improver.generate_improvement_report()
    return {"report": report}


@router.post("/experiments/ab-test", dependencies=[Depends(check_admin_auth)])
async def ab_test(req: ABTestRequest):
    from agents.intelligence.ab_tester import ABTester

    tester = ABTester()
    result = tester.run_comparison(
        req.prompt_id, req.prompt_a, req.prompt_b, req.test_cases
    )
    return result


@router.post("/registry/review", dependencies=[Depends(check_admin_auth)])
async def registry_review(req: RegistryReviewRequest):
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_openai import ChatOpenAI

    from agents.prompts.registry import PROMPT_REGISTRY
    from config import settings

    entry = PROMPT_REGISTRY.get("MED-GOV-REGISTRY-001")
    if not entry:
        raise HTTPException(status_code=500, detail="Registry review prompt missing")
    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL, temperature=0.0, api_key=settings.OPENAI_API_KEY
    )
    prompt = entry.content.format(
        old_hash=req.old_hash, new_hash=req.new_hash, delta_report=req.delta_report
    )
    resp = llm.invoke(
        [
            SystemMessage(content="You are the Prompt Registry Governance Engine."),
            HumanMessage(content=prompt),
        ]
    )
    return {"review": resp.content}


@router.post("/admin/override-escalation", dependencies=[Depends(check_admin_auth)])
async def override_escalation(req: OverrideEscalationRequest):
    from database.models import Interaction, ReviewStatus

    pers = get_persistence()
    inter = (
        pers.db.query(Interaction).filter(Interaction.id == req.interaction_id).first()
    )
    if not inter:
        raise HTTPException(status_code=404, detail="Interaction not found")
    inter.requires_human_review = not req.override
    inter.review_status = (
        ReviewStatus.APPROVED if req.override else ReviewStatus.FLAGGED
    )
    inter.reviewer_comment = req.rationale
    pers.db.commit()
    return {"status": "ok", "requires_human_review": inter.requires_human_review}


@router.post("/admin/audit-export", dependencies=[Depends(check_admin_auth)])
async def audit_export(req: AuditExportRequest):
    from database.models import AuditLog, Interaction

    pers = get_persistence()
    gov = get_governance()
    data = {}
    if req.interaction_id:
        inter = (
            pers.db.query(Interaction)
            .filter(Interaction.id == req.interaction_id)
            .first()
        )
        if not inter:
            raise HTTPException(status_code=404, detail="Interaction not found")
        data["interaction"] = {
            "id": inter.id,
            "timestamp": str(inter.timestamp),
            "audit_hash": inter.audit_hash,
            "model_used": inter.model_used,
            "prompt_version": inter.prompt_version,
            "risk_level": inter.risk_level,
            "confidence_score": inter.confidence_score,
        }
    # include recent audit logs summary
    logs = pers.db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(10).all()
    data["audit_logs"] = [
        {
            "time": str(l.timestamp),
            "actor": l.actor_id,
            "action": l.action,
            "status": l.status,
        }
        for l in logs
    ]
    return data
