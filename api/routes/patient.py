"""
Clinical Data Hub - Reports, Medications, and Calendar.
"""
from fastapi import APIRouter, HTTPException, Depends
from agents.persistence_agent import PersistenceAgent
from agents.report_agent import ReportAgent
from agents.medication_agent import MedicationAgent
from agents.calendar_agent import CalendarAgent

router = APIRouter(prefix="/data", tags=["Patient Data"])

@router.get("/reports")
async def get_reports(user_id: str):
    agent = ReportAgent()
    return await agent.get_user_reports(user_id)

@router.get("/reports/{report_id}")
async def get_report_by_id(report_id: int):
    agent = ReportAgent()
    return await agent.get_report(report_id)

@router.get("/history")
async def get_interaction_history(user_id: str):
    agent = PersistenceAgent()
    return await agent.get_history(user_id)

@router.get("/medications")
async def get_medications(user_id: str):
    agent = MedicationAgent()
    return await agent.get_medications(user_id)

@router.get("/appointments")
async def get_appointments():
    agent = CalendarAgent()
    return await agent.list_upcoming_events()

@router.get("/reminders")
async def get_reminders(user_id: str):
    # Simulated integration with notification engine/database
    from notifications.engine import notification_engine
    return {"reminders": ["Take aspirin at 8 PM", "Blood pressure check at 10 AM"]}
