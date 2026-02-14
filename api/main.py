"""
FastAPI Backend for MedAgent - Enhanced Command Center.
Includes Admin Routes, System Health, and Governance Controls.
Updated for Feedback & Review.
"""
import sys
import os
from pathlib import Path
from typing import List

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, field_validator
from typing import Optional, Dict

from agents.orchestrator import MedAgentOrchestrator
from agents.persistence_agent import PersistenceAgent
from agents.governance_agent import GovernanceAgent
from agents.self_improvement_agent import SelfImprovementAgent
from agents.developer_agent import DeveloperControlAgent
from config import settings
from utils.safety import validate_medical_input, sanitize_input

# API Key Auth (Simulated)
API_KEY_NAME = "X-Admin-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def check_admin_auth(api_key: str = Depends(api_key_header)):
    expected_key = os.getenv("ADMIN_API_KEY", "admin-secret-dev") 
    if api_key != expected_key:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Auth Failed")
    return True

app = FastAPI(title="MedAgent Global API", version="5.0.0-SELF-IMPROVING")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/")
async def root():
    return {"status": "Online", "version": "5.0.0"}

@app.get("/health")
async def health():
    return {"status": "ok", "version": "5.0.0"}

@app.get("/ready")
async def ready():
    try:
        orch = get_orchestrator()
        if orch:
            return {"status": "ready", "version": "5.0.0"}
    except Exception:
        pass
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=503, content={"status": "not_ready", "version": "5.0.0"})

# Global Singletons
_orchestrator = None
_persistence = None
_governance = None
_improver = None
_developer_agent = None

def get_orchestrator():
    global _orchestrator
    if _orchestrator is None:
         _orchestrator = MedAgentOrchestrator()
    return _orchestrator

def get_persistence():
    global _persistence
    if _persistence is None: _persistence = PersistenceAgent()
    return _persistence

def get_governance():
    global _governance
    if _governance is None: _governance = GovernanceAgent()
    return _governance

def get_improver():
    global _improver
    if _improver is None: _improver = SelfImprovementAgent()
    return _improver

def get_developer_agent(): # Added developer agent getter
    global _developer_agent
    if _developer_agent is None: _developer_agent = DeveloperControlAgent()
    return _developer_agent

# --- DEVELOPER/SYSTEM ROUTES ---
@app.get("/system/health", dependencies=[Depends(check_admin_auth)])
async def system_health():
    """Get aggregated system health metrics."""
    developer_agent = get_developer_agent()
    return developer_agent.get_system_health()

@app.post("/system/register-dev", dependencies=[Depends(check_admin_auth)])
async def register_dev(username: str):
    """Register a new developer (simulated)."""
    developer_agent = get_developer_agent()
    return developer_agent.register_developer(username=username)

@app.get("/system/test", dependencies=[Depends(check_admin_auth)])
async def trigger_tests():
    """Run full system test suite."""
    developer_agent = get_developer_agent()
    return developer_agent.trigger_system_test()

# --- MODELS ---
class PatientRequest(BaseModel):
    symptoms: str
    patient_id: str = "GUEST"

    @field_validator('symptoms')
    @classmethod
    def symptoms_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Symptoms must not be empty')
        return v

class FeedbackRequest(BaseModel):
    session_id: str
    rating: int
    comment: Optional[str] = None

class AgentResponse(BaseModel):
    summary: Optional[str] = None
    diagnosis: Optional[str] = None
    appointment: Optional[str] = None
    doctor_review: Optional[str] = None
    is_emergency: bool = False
    medical_report: Optional[str] = None
    doctor_summary: Optional[str] = None
    patient_instructions: Optional[str] = None
    language: str = "en"
    requires_human_review: bool = False

class AdminReviewAction(BaseModel):
    interaction_id: int
    action: str # APPROVE, REJECT
    comment: Optional[str] = None

# --- PUBLIC ROUTES ---
@app.post("/consult")
async def consult(request: PatientRequest):
    try:
        orch = get_orchestrator()
        result = orch.run(request.symptoms, user_id=request.patient_id)
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("final_response"))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback")
async def submit_feedback(fb: FeedbackRequest):
    """Submit user feedback for Self-Improvement."""
    # Logic to save feedback to DB (Simplified: usually persistence agent handles this)
    # We would add a save_feedback method to persistence_agent.
    return {"status": "received", "message": "Thank you for your feedback!"}

# --- ADMIN ROUTES ---
@app.get("/admin/pending-reviews", dependencies=[Depends(check_admin_auth)])
async def get_pending_reviews():
    """Get interactions flagged for human review."""
    # Mock return - usually fetch from DB where review_status='pending'
    return [{"id": 1, "input": "...", "response": "..."}]

@app.post("/admin/review-action", dependencies=[Depends(check_admin_auth)])
async def review_action(action: AdminReviewAction):
    """Approve or Reject a flagged response."""
    # Logic to update DB status
    return {"status": "updated", "action": action.action}

@app.get("/admin/improvement-report", dependencies=[Depends(check_admin_auth)])
async def improvement_report():
    """Get Self-Improvement analysis."""
    improver = get_improver()
    report = improver.generate_improvement_report()
    return {"report": report}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
