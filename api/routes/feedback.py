from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional, List, Dict
import datetime

from agents.persistence_agent import PersistenceAgent
from agents.feedback_safety_layer import feedback_safety
from api.deps import get_persistence, get_current_user

router = APIRouter(prefix="/feedback", tags=["Feedback"])

class FeedbackSubmission(BaseModel):
    case_id: str
    rating: int # 0-5
    ai_response: str
    comment: Optional[str] = None
    corrected_response: Optional[str] = None # Doctor only

@router.post("/", status_code=status.HTTP_201_CREATED)
async def submit_feedback(fb: FeedbackSubmission, user: dict = Depends(get_current_user)):
    """Submit clinical feedback for AI improvement."""
    pers = get_persistence()
    
    # 1. Basic Safety & Heuristics Check (Phase 8)
    if not feedback_safety.check_feedback_safety(fb.rating, fb.comment or ""):
         raise HTTPException(status_code=400, detail="Feedback rejected due to safety heuristics (e.g., invalid rating or length).")

    # 2. Validate Role-specific fields & Doctor Authority (Phase 8)
    role = user.get("role", "patient")
    if fb.corrected_response:
        if role != "doctor":
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Only doctors can provide corrected clinical responses."
            )
        
        # Rigorous verification check (Phase 8)
        is_verified = await feedback_safety.validate_doctor_authority(user)
        if not is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Medical corrections require verified doctor credentials."
            )
    
    # 3. Save Feedback
    fb_id = await pers.save_feedback(
        user_id=user["sub"],
        role=role,
        case_id=fb.case_id,
        ai_response=fb.ai_response,
        rating=fb.rating,
        comment=fb.comment,
        corrected_response=fb.corrected_response if role == "doctor" else None
    )
    
    if not fb_id:
        raise HTTPException(status_code=500, detail="Failed to save feedback.")
    
    return {"status": "success", "feedback_id": fb_id, "message": "Feedback received and processed for learning."}

@router.get("/{case_id}")
async def get_feedback(case_id: str, user: dict = Depends(get_current_user)):
    """Retrieve feedback for a specific medical case."""
    pers = get_persistence()
    feedback = await pers.get_feedback_by_case(case_id)
    return feedback

@router.get("/analytics/summary")
async def get_analytics(user: dict = Depends(get_current_user)):
    """Get aggregated feedback analytics (Admin/Doctor restricted)."""
    if user.get("role") not in ["doctor", "admin"]:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
         
    pers = get_persistence()
    analytics = await pers.get_feedback_analytics()
    return analytics
