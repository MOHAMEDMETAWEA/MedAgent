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
from pydantic import BaseModel
from typing import Optional, Dict

from agents.orchestrator import MedAgentOrchestrator
from agents.persistence_agent import PersistenceAgent
from agents.governance_agent import GovernanceAgent
from agents.self_improvement_agent import SelfImprovementAgent
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

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_tokens=True, allow_methods=["*"], allow_headers=["*"])

# Global Singletons
_orchestrator = None
_persistence = None
_governance = None
_improver = None

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

# --- MODELS ---
class PatientRequest(BaseModel):
    symptoms: str
    patient_id: str = "GUEST"

class FeedbackRequest(BaseModel):
    session_id: str
    rating: int
    comment: Optional[str] = None

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
