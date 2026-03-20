"""
Clinical Consultation & Image Analysis Routes.
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, BackgroundTasks
from pydantic import BaseModel, field_validator
from typing import Optional, Dict
import uuid
import time
from agents.orchestrator import MedAgentOrchestrator

router = APIRouter(tags=["Clinical"])

class PatientRequest(BaseModel):
    symptoms: str
    patient_id: str = "GUEST"
    image_path: Optional[str] = None
    request_second_opinion: bool = False
    interaction_mode: Optional[str] = None

    @field_validator('symptoms')
    @classmethod
    def symptoms_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Symptoms must not be empty')
        return v

def get_orchestrator():
    return MedAgentOrchestrator()

@router.post("/consult")
async def consult(request: PatientRequest):
    orch = get_orchestrator()
    t0 = time.perf_counter()
    # Execute core graph asynchronously
    result = await orch.run(
        request.symptoms, 
        user_id=request.patient_id, 
        image_path=request.image_path,
        request_second_opinion=request.request_second_opinion,
        interaction_mode=request.interaction_mode
    )
    latency = int((time.perf_counter() - t0) * 1000)
    result["latency_ms"] = latency
    
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("final_response", "Invalid input"))
        
    return result
