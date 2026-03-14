from pydantic import BaseModel, EmailStr
from typing import Optional

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

payload = {
    "username": "testuser_abc",
    "email": "test_abc@medagent.com", # Use .com just in case
    "phone": "555-abc",
    "password": "SecurePassword123!",
    "full_name": "Auditor Test User",
    "role": "patient",
    "age": 30,
    "gender": "Male",
    "country": "Egypt"
}

try:
    req = RegisterRequest(**payload)
    print("Validation Success")
except Exception as e:
    print(f"Validation Error: {e}")
