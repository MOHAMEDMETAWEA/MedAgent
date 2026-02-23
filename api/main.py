"""
FastAPI Backend for MedAgent - Enhanced Command Center.
Includes Admin Routes, System Health, and Governance Controls.
Updated for Feedback, Review, and Medical Image Analysis.
"""
import sys
import os
import uuid
import datetime
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from fastapi import FastAPI, HTTPException, Request, Depends, status, File, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from pydantic import BaseModel, field_validator, EmailStr

from agents.orchestrator import MedAgentOrchestrator
from agents.persistence_agent import PersistenceAgent
from agents.governance_agent import GovernanceAgent
from agents.self_improvement_agent import SelfImprovementAgent
from agents.developer_agent import DeveloperControlAgent
from agents.authentication_agent import AuthenticationAgent
from agents.human_review_agent import HumanReviewAgent
from agents.medication_agent import MedicationAgent
from agents.report_agent import ReportAgent
from agents.calendar_agent import CalendarAgent
from config import settings
from utils.safety import validate_medical_input, sanitize_input

logger = logging.getLogger(__name__)

# API Key Auth (Simulated)
API_KEY_NAME = "X-Admin-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def check_admin_auth(api_key: str = Depends(api_key_header)):
    expected_key = os.getenv("ADMIN_API_KEY", "admin-secret-dev") 
    if api_key != expected_key:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Auth Failed")
    return True

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    gov = get_governance()
    payload = gov.verify_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return payload

app = FastAPI(title="MedAgent Global System", version="5.3.0-PRODUCTION")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/")
async def root():
    return {"status": "Online", "version": "5.3.0"}

@app.get("/health")
async def health():
    return {"status": "ok", "version": "5.3.0"}

@app.get("/ready")
async def ready():
    try:
        orch = get_orchestrator()
        if orch:
            return {"status": "ready", "version": "5.3.0"}
    except Exception:
        pass
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=503, content={"status": "not_ready", "version": "5.3.0"})

UPLOAD_DIR = _root / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_IMAGE_FORMATS = ["jpg", "jpeg", "png", "webp", "heic", "dicom", "dcm"]
MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # 20MB

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """Securely upload a medical image with metadata storage."""
    try:
        file_ext = file.filename.split(".")[-1].lower()
        if file_ext not in ALLOWED_IMAGE_FORMATS:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported format. Allowed: {', '.join(ALLOWED_IMAGE_FORMATS)}"
            )
        
        # Read file content
        content = await file.read()
        
        # Validate file size
        if len(content) > MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=400, detail="File too large. Maximum 20MB allowed.")
        
        file_name = f"{uuid.uuid4()}.{file_ext}"
        file_path = UPLOAD_DIR / file_name
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        return {
            "image_path": str(file_path), 
            "filename": file.filename,
            "size_bytes": len(content),
            "format": file_ext
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

from agents.verification_agent import VerificationAgent

# Global Singletons
_orchestrator = None
_persistence = None
_governance = None
_improver = None
_developer_agent = None
_auth_agent = None
_review_agent = None
_medication_agent = None
_report_agent = None
_calendar_agent = None
_verification_agent = None

def get_verification_agent():
    global _verification_agent
    if _verification_agent is None: _verification_agent = VerificationAgent()
    return _verification_agent

def get_orchestrator():
    global _orchestrator
    if _orchestrator is None:
         _orchestrator = MedAgentOrchestrator()
    return _orchestrator

def get_persistence():
    global _persistence
    if _persistence is None: _persistence = PersistenceAgent()
    return _persistence

def get_governance():
    global _governance
    if _governance is None: _governance = GovernanceAgent()
    return _governance

def get_improver():
    global _improver
    if _improver is None: _improver = SelfImprovementAgent()
    return _improver

def get_developer_agent():
    global _developer_agent
    if _developer_agent is None: _developer_agent = DeveloperControlAgent()
    return _developer_agent

def get_auth_agent():
    global _auth_agent
    if _auth_agent is None: _auth_agent = AuthenticationAgent()
    return _auth_agent

def get_review_agent():
    global _review_agent
    if _review_agent is None: _review_agent = HumanReviewAgent()
    return _review_agent

def get_medication_agent():
    global _medication_agent
    if _medication_agent is None: _medication_agent = MedicationAgent()
    return _medication_agent

def get_report_agent():
    global _report_agent
    if _report_agent is None: _report_agent = ReportAgent()
    return _report_agent

def get_calendar_agent():
    global _calendar_agent
    if _calendar_agent is None: _calendar_agent = CalendarAgent()
    return _calendar_agent

# --- DEVELOPER/SYSTEM ROUTES ---
@app.get("/system/health", dependencies=[Depends(check_admin_auth)])
async def system_health():
    """Get aggregated system health metrics."""
    developer_agent = get_developer_agent()
    return developer_agent.get_system_health()

@app.post("/system/register-dev", dependencies=[Depends(check_admin_auth)])
async def register_dev(username: str):
    """Register a new developer (simulated)."""
    developer_agent = get_developer_agent()
    return developer_agent.register_developer(username=username)

@app.get("/system/test", dependencies=[Depends(check_admin_auth)])
async def trigger_tests():
    """Run full system test suite."""
    developer_agent = get_developer_agent()
    return developer_agent.trigger_system_test()

@app.get("/system/capabilities")
async def get_capabilities():
    """List all active agents and generative capabilities (Bilingual)."""
    return {
        "agents": [
            {"name": "Triage Agent / عميل الفرز", "role": "Analyzes symptoms and severity / يحلل الأعراض والخطورة"},
            {"name": "Knowledge Agent / عميل المعرفة", "role": "Retrieves medical literature via RAG / يسترجع الأدبيات الطبية"},
            {"name": "Reasoning Agent / عميل التفكير", "role": "Performs differential analysis / يقوم بالتحليل التفريقي"},
            {"name": "Safety Agent / عميل السلامة", "role": "Check for errors and safety / يتحقق من الأخطاء والسلامة"},
            {"name": "Validation Agent / عميل التحقق", "role": "Verifies medical accuracy / يتحقق من الدقة الطبية"},
            {"name": "Vision Analysis Agent / عميل تحليل الصور", "role": "Analyzes medical images (X-ray, Rashes, etc.) / يحلل الصور الطبية (الأشعة، الأمراض الجلدية، إلخ)"},
            {"name": "Patient Agent / عميل المريض", "role": "Manages patient profile and history / يدير ملف المريض وتاريخه"},
            {"name": "Report Agent / عميل التقارير", "role": "Generates medical reports / ينشئ التقارير الطبية"},
            {"name": "Calendar Agent / عميل التقويم", "role": "Manages appointments / يدير المواعيد"},
            {"name": "Supervisor Agent / عميل الإشراف", "role": "Monitors system health / يراقب صحة النظام"},
            {"name": "Self-Improvement Agent / عميل التحسين الذاتي", "role": "Learns from feedback / يتعلم من التعليقات"},
            {"name": "Developer Control Agent / عميل التحكم المطور", "role": "System management for devs / إدارة النظام للمطورين"},
            {"name": "Medication Agent / عميل الأدوية", "role": "Tracks dosages and reminders / يتتبع الجرعات والتذكيرات"},
            {"name": "Second Opinion Agent / عميل الرأي الثاني", "role": "Independent diagnostic audit / تدقيق تشخيصي مستقل"},
            {"name": "Human Review Agent / عميل المراجعة البشرية", "role": "Clinician-in-the-loop audit / مراجعة الطبيب المختص"},
            {"name": "Verification Agent / عميل التحقق", "role": "Validates doctor licenses / يتحقق من تراخيص الأطباء"},
            {"name": "Authentication Agent / عميل الهوية", "role": "Secure JWT management / إدارة الهوية الآمنة"},
            {"name": "Persistence Agent / عميل الاستمرارية", "role": "Manages medical memory graph / يدير سجل الذاكرة الطبية"},
            {"name": "Governance Agent / عميل الحوكمة", "role": "AES-256 encryption authority / سلطة التشفير والحوكمة"}
        ],
        "capabilities": [
            {"id": "IMAGE_ANALYSIS", "label": "Medical Image Analysis / تحليل الصور الطبية", "generative": True},
            {"id": "GENERATE_REPORT", "label": "Generate Report / إنشاء تقرير", "generative": True},
            {"id": "GENERATE_RECOMMENDATION", "label": "Generate Recommendation / إنشاء توصية", "generative": True},
            {"id": "BOOK_APPOINTMENT", "label": "Book Appointment / حجز موعد", "generative": False},
            {"id": "RETRIEVE_HISTORY", "label": "Retrieval History / استرجاع السجل", "generative": False},
            {"id": "DATA_EXPORT", "label": "Data Export / تصدير البيانات", "generative": False},
            {"id": "MEMORY_GRAPH", "label": "Memory Graph / سجل الذاكرة", "generative": False},
            {"id": "RAG_INSIGHTS", "label": "RAG Context / سياق المعرفة Retrieval Augmented Generation", "generative": False},
            {"id": "TREE_OF_THOUGHT", "label": "Clinical Reasoning (ToT) / التفكير السريري", "generative": True}
        ]
    }

class UserActionRequest(BaseModel):
    session_id: str
    action_type: str
    element_id: str
    details: Optional[Dict] = None

@app.post("/system/log-action")
async def log_action(request: UserActionRequest):
    """Log a granular user UI action."""
    pers = get_persistence()
    success = pers.save_user_action(
        session_id=request.session_id,
        action_type=request.action_type,
        element_id=request.element_id,
        details=request.details or {}
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to log action")
    return {"status": "logged"}

# --- AUTH MODELS ---
class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    phone: str
    password: str
    full_name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    country: Optional[str] = None
    role: str = "patient" # patient or doctor

class VerifyDoctorRequest(BaseModel):
    license_number: str
    specialization: str

class ModeRequest(BaseModel):
    interaction_mode: str # patient or doctor

class LoginRequest(BaseModel):
    login_id: str # username, email, or phone
    password: str

# --- AUTH ROUTES ---
@app.post("/auth/register")
async def register(req: RegisterRequest):
    pers = get_persistence()
    # Check for duplicates (Simplified)
    if pers.get_user_by_login(req.username) or pers.get_user_by_login(req.email) or pers.get_user_by_login(req.phone):
        raise HTTPException(status_code=400, detail="Account with this username/email/phone already exists")
    
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
        meta={"age": req.age, "gender": req.gender}
    )
    if not user_id:
        raise HTTPException(status_code=500, detail="Registration failed")
    return {"status": "success", "user_id": user_id}

@app.post("/auth/set-mode")
async def set_interaction_mode(req: ModeRequest, user: dict = Depends(get_current_user)):
    pers = get_persistence()
    success = pers.update_interaction_mode(user["sub"], req.interaction_mode)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update mode")
    return {"status": "success", "mode": req.interaction_mode}

@app.post("/auth/verify-doctor")
async def verify_doctor(req: VerifyDoctorRequest, user: dict = Depends(get_current_user)):
    agent = get_verification_agent()
    # We need country from user account
    pers = get_persistence()
    from database.models import UserAccount
    db_user = pers.db.query(UserAccount).filter(UserAccount.id == user["sub"]).first()
    country = db_user.country if db_user else "Unknown"
    
    success, message = agent.verify_doctor_credentials(user["sub"], req.license_number, req.specialization, country)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"status": "verified", "message": message}

@app.post("/auth/login")
async def login(req: LoginRequest, request: Request):
    auth_agent = get_auth_agent()
    result, error = auth_agent.validate_login(req.login_id, req.password, ip=request.client.host)
    if error:
        raise HTTPException(status_code=401, detail=error)
    
    return {
        "access_token": result["token"],
        "token_type": "bearer",
        "user": result["user"],
        "session_id": result["session_id"]
    }

@app.get("/reports")
async def get_reports(user: dict = Depends(get_current_user)):
    agent = get_report_agent()
    return agent.get_user_reports(user["sub"])

@app.get("/reports/{report_id}/export")
async def export_report(report_id: int, format: str = "pdf", user: dict = Depends(get_current_user)):
    pers = get_persistence()
    agent = get_report_agent()
    
    # Get report data
    from database.models import MedicalReport
    report = pers.db.query(MedicalReport).filter(MedicalReport.id == report_id, MedicalReport.patient_id == user["sub"]).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    data = json.loads(pers.governance.decrypt(report.report_content_encrypted))
    
    # Add metadata for professional look
    data["patient_id"] = report.patient_id
    data["date"] = report.generated_at.strftime("%Y-%m-%d %H:%M")
    data["lang"] = report.language
    
    # Generate local path
    import os
    format = format.lower()
    if format == "pdf":
        filename = f"report_{report_id}.pdf"
        media_type = "application/pdf"
        success = agent.generate_pdf(data, os.path.join(settings.DATA_DIR, "uploads", filename))
    elif format == "image" or format == "png":
        filename = f"report_{report_id}.png"
        media_type = "image/png"
        success = agent.generate_image(data, os.path.join(settings.DATA_DIR, "uploads", filename))
    elif format == "text" or format == "txt":
        filename = f"report_{report_id}.txt"
        media_type = "text/plain"
        success = agent.generate_text(data, os.path.join(settings.DATA_DIR, "uploads", filename))
    else:
        raise HTTPException(status_code=400, detail="Unsupported format. Use pdf, image, or text.")

    path = os.path.join(settings.DATA_DIR, "uploads", filename)
    
    if not success:
        raise HTTPException(status_code=500, detail=f"{format.upper()} generation failed")
        
    from fastapi.responses import FileResponse
    return FileResponse(path, filename=filename, media_type=media_type)

@app.get("/auth/export-data")
async def export_user_data(user: dict = Depends(get_current_user)):
    """Export all user records as CSV (Portability)."""
    pers = get_persistence()
    user_id = user["sub"]
    
    # Collect data
    reports = pers.get_reports_by_patient(user_id)
    meds = pers.get_medications(user_id)
    
    import pandas as pd
    import io
    
    # Combine into a simple manifest for CSV
    data = []
    for r in reports:
        data.append({"type": "Medical Report", "date": str(r['generated_at']), "content": str(r['content'])})
    for m in meds:
        data.append({"type": "Medication", "date": "Active", "content": f"{m['name']} {m['dosage']} {m['frequency']}"})
        
    df = pd.DataFrame(data)
    stream = io.StringIO()
    df.to_csv(stream, index=False)
    
    from fastapi.responses import Response
    return Response(content=stream.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=my_health_data.csv"})

@app.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    return user

@app.delete("/auth/account")
async def delete_account(user: dict = Depends(get_current_user)):
    """Delete user account safely."""
    pers = get_persistence()
    success = pers.delete_account(user["sub"])
    if not success:
        raise HTTPException(status_code=500, detail="Deletion failed")
    return {"status": "deleted"}

# --- MEDICATION MODELS ---
class MedicationRequest(BaseModel):
    name: str
    dosage: str
    frequency: str

class ReminderRequest(BaseModel):
    title: str
    time: str
    medication_id: Optional[int] = None

# --- MEDICATION ROUTES ---
@app.post("/medications")
async def add_medication(req: MedicationRequest, user: dict = Depends(get_current_user)):
    agent = get_medication_agent()
    success = agent.add_medication(user["sub"], req.name, req.dosage, req.frequency)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to add medication")
    return {"status": "added"}

@app.get("/medications")
async def get_medications(user: dict = Depends(get_current_user)):
    agent = get_medication_agent()
    return agent.get_medications(user["sub"])

@app.get("/appointments")
async def get_appointments(user: dict = Depends(get_current_user)):
    agent = get_calendar_agent()
    return agent.list_upcoming_events()

@app.post("/reminders")
async def add_reminder(req: ReminderRequest, user: dict = Depends(get_current_user)):
    agent = get_medication_agent()
    success = agent.add_reminder(user["sub"], req.title, req.time, req.medication_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to add reminder")
    return {"status": "added"}

# --- MODELS ---
class PatientRequest(BaseModel):
    symptoms: str
    patient_id: str = "GUEST"
    image_path: Optional[str] = None
    request_second_opinion: bool = False
    interaction_mode: Optional[str] = None # patient or doctor, overrides default

    @field_validator('symptoms')
    @classmethod
    def symptoms_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Symptoms must not be empty')
        return v

class FeedbackRequest(BaseModel):
    session_id: str
    rating: int
    comment: Optional[str] = None

class AgentResponse(BaseModel):
    summary: Optional[str] = None
    diagnosis: Optional[str] = None
    appointment: Optional[str] = None
    doctor_review: Optional[str] = None
    is_emergency: bool = False
    medical_report: Optional[str] = None
    doctor_summary: Optional[str] = None
    patient_instructions: Optional[str] = None
    language: str = "en"
    requires_human_review: bool = False

class AdminReviewAction(BaseModel):
    interaction_id: int
    action: str # APPROVE, REJECT
    comment: Optional[str] = None

# --- BACKGROUND TASKS ---
async def send_health_alerts(user_id: str, message: str):
    """Simulate push notifications or email alerts."""
    logger.info(f"ALERTS QUEUED for {user_id}: {message}")
    # In a real system, integrate with Twilio/SendGrid here.

# --- PUBLIC ROUTES ---
@app.post("/consult")
async def consult(request: PatientRequest, background_tasks: BackgroundTasks):
    try:
        orch = get_orchestrator()
        result = orch.run(
            request.symptoms, 
            user_id=request.patient_id, 
            image_path=request.image_path,
            request_second_opinion=request.request_second_opinion,
            interaction_mode=request.interaction_mode
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("final_response"))
            
        # Trigger background logic if priority is high
        if result.get("critical_alert"):
            background_tasks.add_task(send_health_alerts, request.patient_id, "EMERGENCY: High risk detected in your consultation.")
            
        return result
    except Exception as e:
        logger.error(f"Consultation failure: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback")
async def submit_feedback(fb: FeedbackRequest):
    """Submit user feedback for Self-Improvement."""
    return {"status": "received", "message": "Thank you for your feedback!"}

# --- IMAGE HISTORY ROUTES ---
@app.get("/images")
async def get_user_images(user: dict = Depends(get_current_user)):
    """List all uploaded medical images with analysis results for the current user."""
    pers = get_persistence()
    try:
        from database.models import MedicalImage
        images = pers.db.query(MedicalImage).filter(
            MedicalImage.patient_id == user["sub"]
        ).order_by(MedicalImage.timestamp.desc()).all()
        
        results = []
        for img in images:
            findings = {}
            if img.visual_findings_encrypted:
                try:
                    findings = json.loads(pers.governance.decrypt(img.visual_findings_encrypted))
                except Exception:
                    findings = {"status": "encrypted"}
            
            results.append({
                "id": img.id,
                "filename": img.original_filename,
                "timestamp": str(img.timestamp),
                "confidence": img.confidence_score,
                "severity": img.severity_level,
                "requires_review": img.requires_human_review,
                "conditions": img.possible_conditions_json or [],
                "findings": findings
            })
        return results
    except Exception as e:
        logger.error(f"Failed to fetch images: {e}")
        return []

@app.get("/images/{image_id}")
async def get_image_detail(image_id: int, user: dict = Depends(get_current_user)):
    """Get detailed analysis for a specific medical image."""
    pers = get_persistence()
    try:
        from database.models import MedicalImage
        img = pers.db.query(MedicalImage).filter(
            MedicalImage.id == image_id,
            MedicalImage.patient_id == user["sub"]
        ).first()
        
        if not img:
            raise HTTPException(status_code=404, detail="Image not found")
        
        findings = {}
        if img.visual_findings_encrypted:
            try:
                findings = json.loads(pers.governance.decrypt(img.visual_findings_encrypted))
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
            "findings": findings
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch image detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- ADMIN ROUTES ---
@app.get("/admin/pending-reviews", dependencies=[Depends(check_admin_auth)])
async def get_pending_reviews():
    """Get interactions flagged for human review."""
    review_agent = get_review_agent()
    gov = get_governance()
    items = review_agent.get_flagged_interactions()
    
    results = []
    for i in items:
        results.append({
            "id": i.id,
            "session_id": i.session_id,
            "user_input": gov.decrypt(i.user_input_encrypted),
            "diagnosis": gov.decrypt(i.diagnosis_output_encrypted),
            "timestamp": i.timestamp
        })
    return results

@app.post("/admin/review-action", dependencies=[Depends(check_admin_auth)])
async def review_action(action: AdminReviewAction):
    """Approve or Reject a flagged response."""
    review_agent = get_review_agent()
    success = review_agent.process_review_action(
        interaction_id=action.interaction_id,
        status=action.action, # APPROVE or REJECT (enum compatible)
        comment=action.comment
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to process review action")
    return {"status": "updated", "action": action.action}

@app.get("/admin/improvement-report", dependencies=[Depends(check_admin_auth)])
async def improvement_report():
    """Get Self-Improvement analysis."""
    improver = get_improver()
    report = improver.generate_improvement_report()
    return {"report": report}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
