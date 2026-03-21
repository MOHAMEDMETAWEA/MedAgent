"""
Authentication & User Management Routes.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr

from agents.authentication_agent import AuthenticationAgent
from agents.persistence_agent import PersistenceAgent

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
    if pers.get_user_by_login(req.username) or pers.get_user_by_login(req.email):
        raise HTTPException(status_code=400, detail="User already exists")

    user_id = pers.register_user(
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
    result, error = auth.validate_login(
        req.login_id, req.password, ip=request.client.host
    )
    if error:
        raise HTTPException(status_code=401, detail=error)
    return result
