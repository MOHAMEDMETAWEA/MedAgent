"""
Clinical Consultation & Image Analysis Routes.
"""

import time
import uuid
from typing import Dict, Optional

from fastapi import (APIRouter, BackgroundTasks, Depends, File, HTTPException,
                     UploadFile)
from pydantic import BaseModel, field_validator

from api.deps import (get_current_user, get_generative_engine,
                      get_orchestrator, get_persistence)

router = APIRouter(prefix="/clinical", tags=["Clinical"])


class PatientRequest(BaseModel):
    symptoms: str
    patient_id: str = "GUEST"
    image_path: Optional[str] = None
    request_second_opinion: bool = False
    interaction_mode: Optional[str] = None

    @field_validator("symptoms")
    @classmethod
    def symptoms_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Symptoms must not be empty")
        return v


class EduRequest(BaseModel):
    topic: str
    audience: str = "patient"
    lang: str = "en"


class PlanRequest(BaseModel):
    diagnosis: str
    patient_profile: dict


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
        interaction_mode=request.interaction_mode,
    )
    latency = int((time.perf_counter() - t0) * 1000)
    result["latency_ms"] = latency

    if result.get("status") == "error":
        raise HTTPException(
            status_code=400, detail=result.get("final_response", "Invalid input")
        )

    return result


@router.post("/generative/education")
async def generate_education(req: EduRequest, user: dict = Depends(get_current_user)):
    gen = get_generative_engine()
    content = gen.generate_educational_content(req.topic, req.audience, req.lang)
    return {"content": content}


@router.post("/generative/care-plan")
async def generate_care_plan(req: PlanRequest, user: dict = Depends(get_current_user)):
    gen = get_generative_engine()
    content = gen.generate_personalized_plan(req.patient_profile, req.diagnosis)
    return {"content": content}


@router.post("/generative/simulation")
async def generate_simulation(condition: str, user: dict = Depends(get_current_user)):
    if user["role"] != "doctor":
        raise HTTPException(
            status_code=403,
            detail="Only doctors can run simulations",
        )
    gen = get_generative_engine()
    content = gen.generate_simulation_scenario(condition)
    return {"simulation": content}


@router.get("/images")
async def get_user_images(user: dict = Depends(get_current_user)):
    """List all uploaded medical images with analysis results for the current user."""
    pers = get_persistence()
    try:
        from database.models import MedicalImage

        images = (
            pers.db.query(MedicalImage)
            .filter(MedicalImage.patient_id == user["sub"])
            .order_by(MedicalImage.timestamp.desc())
            .all()
        )

        results = []
        import json

        for img in images:
            findings = {}
            if img.visual_findings_encrypted:
                try:
                    findings = json.loads(
                        pers.governance.decrypt(img.visual_findings_encrypted)
                    )
                except Exception:
                    findings = {"status": "encrypted"}

            results.append(
                {
                    "id": img.id,
                    "filename": img.original_filename,
                    "timestamp": str(img.timestamp),
                    "confidence": img.confidence_score,
                    "severity": img.severity_level,
                    "requires_review": img.requires_human_review,
                    "conditions": img.possible_conditions_json or [],
                    "findings": findings,
                }
            )
        return results
    except Exception as e:
        import logging

        logging.error(f"Failed to fetch images: {e}")
        return []


@router.get("/images/{image_id}")
async def get_image_detail(image_id: int, user: dict = Depends(get_current_user)):
    """Get detailed analysis for a specific medical image."""
    pers = get_persistence()
    try:
        from database.models import MedicalImage

        img = (
            pers.db.query(MedicalImage)
            .filter(MedicalImage.id == image_id, MedicalImage.patient_id == user["sub"])
            .first()
        )

        if not img:
            raise HTTPException(status_code=404, detail="Image not found")

        import json

        findings = {}
        if img.visual_findings_encrypted:
            try:
                findings = json.loads(
                    pers.governance.decrypt(img.visual_findings_encrypted)
                )
            except Exception:
                findings = {"status": "encrypted"}

        return {
            "id": img.id,
            "filename": img.original_filename,
            "timestamp": str(img.timestamp),
            "confidence": img.confidence_score,
            "severity": img.severity_level,
            "requires_review": img.requires_human_review,
            "conditions": img.possible_conditions_json or [],
            "findings": findings,
        }
    except HTTPException:
        raise
    except Exception as e:
        import logging

        logging.error(f"Failed to fetch image detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))
