"""
Authentication & User Management Routes.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr

from agents.authentication_agent import AuthenticationAgent
from agents.persistence_agent import PersistenceAgent
from api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    phone: str
    password: str
    full_name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    country: Optional[str] = None
    role: str = "patient"


class VerifyDoctorRequest(BaseModel):
    license_number: str
    specialization: str


class ModeRequest(BaseModel):
    interaction_mode: str


class LoginRequest(BaseModel):
    login_id: str
    password: str


def get_auth_agent():
    return AuthenticationAgent()


def get_persistence():
    return PersistenceAgent()


@router.post("/register")
async def register(req: RegisterRequest):
    pers = get_persistence()
    if await pers.get_user_by_login(req.username) or await pers.get_user_by_login(
        req.email
    ):
        raise HTTPException(status_code=400, detail="User already exists")

    user_id = await pers.register_user(
        username=req.username,
        email=req.email,
        phone=req.phone,
        password=req.password,
        full_name=req.full_name,
        role=req.role,
        gender=req.gender,
        age=req.age,
        country=req.country,
    )
    return {"status": "success", "user_id": user_id}


@router.post("/login")
async def login(req: LoginRequest, request: Request):
    auth = get_auth_agent()
    result, error = await auth.validate_login(
        req.login_id, req.password, ip=request.client.host
    )
    if error:
        raise HTTPException(status_code=401, detail=error)
    return result


@router.post("/verify-doctor")
async def verify_doctor(
    req: VerifyDoctorRequest, user: dict = Depends(get_current_user)
):
    pers = get_persistence()
    success = await pers.verify_doctor(
        user["sub"], req.license_number, req.specialization
    )
    if not success:
        raise HTTPException(status_code=500, detail="Verification failed")
    return {"status": "verified"}


@router.post("/set-mode")
async def set_mode(req: ModeRequest, user: dict = Depends(get_current_user)):
    pers = get_persistence()
    success = await pers.update_interaction_mode(user["sub"], req.interaction_mode)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update mode")
    return {"status": "updated"}


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    return user


@router.get("/export-data")
async def export_user_data(user: dict = Depends(get_current_user)):
    """Export all user records as CSV (Portability)."""
    pers = get_persistence()
    user_id = user["sub"]

    reports = await pers.get_reports_by_patient(user_id)
    meds = await pers.get_medications(user_id)

    import io

    import pandas as pd

    data = []
    for r in reports:
        data.append(
            {
                "type": "Medical Report",
                "date": str(r.get("generated_at")),
                "content": str(r.get("content")),
            }
        )
    for m in meds:
        data.append(
            {
                "type": "Medication",
                "date": "Active",
                "content": f"{m.get('name')} {m.get('dosage')} {m.get('frequency')}",
            }
        )

    df = pd.DataFrame(data)
    stream = io.StringIO()
    df.to_csv(stream, index=False)

    from fastapi.responses import Response

    return Response(
        content=stream.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=my_health_data.csv"},
    )


@router.delete("/account")
async def delete_account(user: dict = Depends(get_current_user)):
    """Delete user account safely."""
    pers = get_persistence()
    success = await pers.delete_account(user["sub"])
    if not success:
        raise HTTPException(status_code=500, detail="Deletion failed")
    return {"status": "deleted"}
