"""
Clinical Data Hub - Reports, Medications, and Calendar.
"""

import json
import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from agents.calendar_agent import CalendarAgent
from agents.medication_agent import MedicationAgent
from agents.persistence_agent import PersistenceAgent
from agents.report_agent import ReportAgent
from api.deps import get_current_user, get_persistence, get_report_agent
from config import settings

router = APIRouter(prefix="/data", tags=["Patient Data"])


@router.get("/reports")
async def get_reports(user: dict = Depends(get_current_user)):
    agent = get_report_agent()
    return agent.get_user_reports(user["sub"])


@router.get("/reports/{report_id}/export")
async def export_report(
    report_id: int, format: str = "pdf", user: dict = Depends(get_current_user)
):
    pers = get_persistence()
    agent = get_report_agent()

    # Get report data
    from database.models import MedicalReport

    # Note: Use synchronous query if persistence.db is sync, or async if it's async
    # main.py was using pers.db.query, which suggests sync.
    # But PersistenceAgent methods are async.
    # Let's check how main.py did it. It was using pers.db.query.

    report = (
        pers.db.query(MedicalReport)
        .filter(MedicalReport.id == report_id, MedicalReport.patient_id == user["sub"])
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    data = json.loads(pers.governance.decrypt(report.report_content_encrypted))

    # Add metadata for professional look
    data["patient_id"] = report.patient_id
    data["date"] = report.generated_at.strftime("%Y-%m-%d %H:%M")
    data["lang"] = report.language

    format = format.lower()
    if format == "pdf":
        filename = f"report_{report_id}.pdf"
        media_type = "application/pdf"
        success = agent.generate_pdf(
            data, os.path.join(settings.DATA_DIR, "uploads", filename)
        )
    elif format == "image" or format == "png":
        filename = f"report_{report_id}.png"
        media_type = "image/png"
        success = agent.generate_image(
            data, os.path.join(settings.DATA_DIR, "uploads", filename)
        )
    elif format == "text" or format == "txt":
        filename = f"report_{report_id}.txt"
        media_type = "text/plain"
        success = agent.generate_text(
            data, os.path.join(settings.DATA_DIR, "uploads", filename)
        )
    else:
        raise HTTPException(
            status_code=400, detail="Unsupported format. Use pdf, image, or text."
        )

    path = os.path.join(settings.DATA_DIR, "uploads", filename)

    if not success:
        raise HTTPException(
            status_code=500, detail=f"{format.upper()} generation failed"
        )

    return FileResponse(path, filename=filename, media_type=media_type)


@router.get("/history")
async def get_interaction_history(user: dict = Depends(get_current_user)):
    pers = get_persistence()
    return await pers.get_user_history(user["sub"])


@router.get("/medications")
async def get_medications(user: dict = Depends(get_current_user)):
    pers = get_persistence()
    return await pers.get_medications(user["sub"])


@router.get("/appointments")
async def get_appointments():
    agent = CalendarAgent()
    return await agent.list_upcoming_events()


@router.get("/reminders")
async def get_reminders(user: dict = Depends(get_current_user)):
    # Simulated integration
    return {"reminders": ["Take aspirin at 8 PM", "Blood pressure check at 10 AM"]}
