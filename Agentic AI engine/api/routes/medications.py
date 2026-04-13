"""
Medication & Reminder Management Routes.
Provides endpoints for medication tracking, reminders, and scheduling.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.deps import get_current_user, get_persistence

router = APIRouter(prefix="/medications", tags=["Medications"])


class MedicationAddRequest(BaseModel):
    name: str
    dosage: str
    frequency: str


class ReminderAddRequest(BaseModel):
    title: str
    time: str
    medication_id: Optional[int] = None


class ScheduleRequest(BaseModel):
    medication_id: int
    times: list  # e.g. ["08:00", "20:00"]


@router.get("/")
async def list_medications(user: dict = Depends(get_current_user)):
    """List all active medications for the current user."""
    pers = get_persistence()
    meds = await pers.get_medications_list(user["sub"])
    return meds


@router.post("/")
async def add_medication(
    req: MedicationAddRequest, user: dict = Depends(get_current_user)
):
    """Add a new medication."""
    pers = get_persistence()
    med_id = await pers.add_medication(user["sub"], req.name, req.dosage, req.frequency)
    if med_id is None:
        raise HTTPException(status_code=500, detail="Failed to add medication")
    return {"status": "success", "medication_id": med_id}


@router.delete("/{med_id}")
async def deactivate_medication(med_id: int, user: dict = Depends(get_current_user)):
    """Deactivate a medication."""
    pers = get_persistence()
    success = await pers.deactivate_medication(user["sub"], med_id)
    if not success:
        raise HTTPException(status_code=404, detail="Medication not found")
    return {"status": "deactivated"}


@router.get("/reminders")
async def list_reminders(user: dict = Depends(get_current_user)):
    """List all active reminders for the current user."""
    pers = get_persistence()
    rems = await pers.get_reminders(user["sub"])
    return rems


@router.post("/reminders")
async def add_reminder(req: ReminderAddRequest, user: dict = Depends(get_current_user)):
    """Add a new reminder."""
    pers = get_persistence()
    rem_id = await pers.add_reminder(
        user["sub"], req.title, req.time, req.medication_id
    )
    if rem_id is None:
        raise HTTPException(status_code=500, detail="Failed to add reminder")
    return {"status": "success", "reminder_id": rem_id}


@router.post("/schedule")
async def schedule_medication(
    req: ScheduleRequest, user: dict = Depends(get_current_user)
):
    """Create reminders for each scheduled time for a medication."""
    pers = get_persistence()
    # Get the medication to use its name in the reminder title
    meds = await pers.get_medications_list(user["sub"])
    med_name = "Medication"
    for m in meds:
        if m["id"] == req.medication_id:
            med_name = m["name"]
            break

    created = []
    for t in req.times:
        rem_id = await pers.add_reminder(
            user["sub"],
            f"Take {med_name}",
            t,
            req.medication_id,
        )
        if rem_id:
            created.append({"reminder_id": rem_id, "time": t})

    return {"status": "success", "schedules_created": created}
