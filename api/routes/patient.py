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
    return agent.get_user_reports(user_id)

@router.get("/medications")
async def get_medications(user_id: str):
    agent = MedicationAgent()
    return agent.get_medications(user_id)

@router.get("/appointments")
async def get_appointments():
    agent = CalendarAgent()
    return agent.list_upcoming_events()
