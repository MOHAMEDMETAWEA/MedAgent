"""
FastAPI Backend for MedAgent - Enhanced Command Center.
Includes Admin Routes, System Health, and Governance Controls.
Updated for Feedback, Review, and Medical Image Analysis.
"""
import sys
print("DEBUG: Importing api.main", file=sys.stderr)
import os
import uuid
import datetime
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict
from contextlib import asynccontextmanager

import bcrypt
# Monkeypatch bcrypt for passlib compatibility in newer versions
if not hasattr(bcrypt, "__about__"):
    class BcryptAbout:
        __version__ = getattr(bcrypt, "__version__", "unknown")
    bcrypt.__about__ = BcryptAbout()


_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from fastapi import FastAPI, HTTPException, Request, Depends, status, File, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from pydantic import BaseModel, field_validator, EmailStr
from jose import jwt, JWTError
import httpx

from agents.orchestrator import MedAgentOrchestrator
from agents.persistence_agent import PersistenceAgent
from agents.governance_agent import GovernanceAgent
from agents.self_improvement_agent import SelfImprovementAgent
from agents.developer_agent import DeveloperControlAgent
from agents.authentication_agent import AuthenticationAgent
from agents.human_review_agent import HumanReviewAgent
from agents.medication_agent import MedicationAgent
from agents.calendar_agent import CalendarAgent
from agents.generative_engine_agent import GenerativeEngineAgent
from agents.report_agent import ReportAgent
from agents.audit_agent import AuditAgent
from agents.export_agent import ExportAgent
from agents.interop.fhir_hl7_builder import InteropBuilder
from config import settings
from api.routes import imaging
from utils.safety import validate_medical_input, sanitize_input
from utils.rate_limit import check_rate_limit, get_client_identifier
import time
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Hospital Performance Metrics
HOSPITAL_LOAD = Gauge("medagent_hospital_concurrent_users", "Number of concurrent clinical sessions")
SAFETY_INCIDENTS = Counter("medagent_safety_blocks_total", "Total count of unsafe advice blocks")
EHR_SYNC_LATENCY = Histogram("medagent_ehr_sync_seconds", "Latency of FHIR data synchronization")
CLINICAL_ERROR_RATE = Counter("medagent_clinical_errors_total", "Total clinical exceptions tracked")

from fastapi.responses import Response
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter

logger = logging.getLogger(__name__)

from api.deps import (
    get_orchestrator, get_persistence, get_governance, get_auth_agent, 
    get_improver, get_developer_agent, get_review_agent, get_medication_agent, 
    get_report_agent, get_calendar_agent, get_verification_agent, 
    get_generative_engine, get_interop_builder, get_audit_agent, 
    get_export_agent, get_current_user, oauth2_scheme, check_admin_auth
)
from api.routes import auth, clinical, patient, governance, system, imaging, feedback, learning, ehr

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting MedAgent Global System (Modern Lifespan)...")
    # Strict Secret Verification
    if not settings.OPENAI_API_KEY or "your-openai-key" in settings.OPENAI_API_KEY:
        logger.critical("PRODUCTION BLOCKER: OPENAI_API_KEY is missing or invalid.")
    if not settings.JWT_SECRET_KEY:
        logger.critical("PRODUCTION BLOCKER: JWT_SECRET_KEY is missing.")
    if not settings.DATA_ENCRYPTION_KEY:
        logger.critical("PRODUCTION BLOCKER: DATA_ENCRYPTION_KEY is missing.")
    yield
    logger.info("Shutting down MedAgent Global System...")

app = FastAPI(title="MedAgent Global System", version="5.3.0-PRODUCTION", lifespan=lifespan)

# Register Modular Routers
app.include_router(auth.router)
app.include_router(clinical.router)
app.include_router(patient.router)
app.include_router(governance.router)
app.include_router(system.router)
app.include_router(imaging.router)
app.include_router(feedback.router)
app.include_router(learning.router)
app.include_router(ehr.router)

app.add_middleware(
    CORSMiddleware, 
    allow_origins=settings.CORS_ALLOWED_ORIGINS, 
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"]
)

# Observability (Retained in main for global context)
REQUEST_LATENCY = Histogram("medagent_request_latency_ms", "Request latency in ms", buckets=[50,100,200,500,1000,2000,5000])
REQUEST_ERRORS = Counter("medagent_request_errors_total", "Total request errors")
ESCALATIONS = Counter("medagent_escalations_total", "Total critical escalations")
MODEL_USAGE = Counter("medagent_model_usage_total", "Model usage counter", ["model"])

# Minimal OpenTelemetry setup (console exporter)
try:
    trace.set_tracer_provider(TracerProvider())
    tracer_provider = trace.get_tracer_provider()
    tracer_provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    tracer = trace.get_tracer("medagent.api")
except Exception:
    tracer = None

@app.get("/")
async def root():
    return {"status": "Online", "version": "5.3.0"}

@app.get("/health")
async def health():
    return {"status": "ok", "version": "5.3.0"}

@app.get("/health/live")
async def health_live():
    return {"status": "live"}

@app.get("/health/ready")
async def health_ready():
    return await ready()

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
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

# Dependencies are now imported from api.deps

# --- DEVELOPER/SYSTEM ROUTES ---
@app.get("/system/health", dependencies=[Depends(check_admin_auth)])
async def system_health():
    """Get aggregated system health metrics."""
    developer_agent = get_developer_agent()
    return developer_agent.get_system_health()

@app.get("/system/audit-logs", dependencies=[Depends(check_admin_auth)])
async def get_audit_logs(limit: int = 100):
    """Retrieve system audit logs."""
    audit = get_audit_agent()
    return audit.get_logs(limit=limit)

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
            {"name": "Governance Agent / عميل الحوكمة", "role": "AES-256 encryption authority / سلطة التشفير والحوكمة"},
            {"name": "Evolution Agent / عميل التطور", "role": "Autonomous medical model fine-tuning / التطوير الذاتي للنماذج الطبية"}
        ],
        "capabilities": [
            {"id": "AUTONOMOUS_LEARNING", "label": "Autonomous Model Evolution / التطور الذاتي للنماذج", "generative": True},
            {"id": "EHR_INTEROPERABILITY", "label": "EHR/FHIR Integration / التكامل مع السجلات الإلكترونية", "generative": False},
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

# --- INTEROPERABILITY ROUTES ---
class InteropRequest(BaseModel):
    report_id: int

@app.post("/interop/fhir")
async def export_fhir(req: InteropRequest, user: dict = Depends(get_current_user)):
    pers = get_persistence()
    gov = get_governance()
    from database.models import MedicalReport, Interaction
    # Fetch report and related interaction/session
    report = pers.db.query(MedicalReport).filter(MedicalReport.id == req.report_id, MedicalReport.patient_id == user["sub"]).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    # Build clinical data from decrypted report content and minimal metadata
    content = json.loads(gov.decrypt(report.report_content_encrypted))
    clinical_data = {
        "patient_id": report.patient_id,
        "generated_at": str(report.generated_at),
        "language": report.language,
        "report": content
    }
    builder = get_interop_builder()
    fhir = builder.build_fhir_bundle(clinical_data)
    if isinstance(fhir, dict) and fhir.get("error"):
        raise HTTPException(status_code=500, detail=fhir["error"])
    return JSONResponse(content=fhir)

@app.post("/interop/hl7")
async def export_hl7(req: InteropRequest, user: dict = Depends(get_current_user)):
    pers = get_persistence()
    gov = get_governance()
    from database.models import MedicalReport
    report = pers.db.query(MedicalReport).filter(MedicalReport.id == req.report_id, MedicalReport.patient_id == user["sub"]).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    content = json.loads(gov.decrypt(report.report_content_encrypted))
    interaction_data = {
        "patient_id": report.patient_id,
        "generated_at": str(report.generated_at),
        "language": report.language,
        "report": content
    }
    builder = get_interop_builder()
    hl7 = builder.build_hl7_v2(interaction_data)
    if isinstance(hl7, str) and hl7.startswith("ERROR:"):
        raise HTTPException(status_code=500, detail=hl7)
    return JSONResponse(content={"hl7": hl7})

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
    interaction_mode: str = "patient"

class AdminReviewAction(BaseModel):
    interaction_id: int
    action: str # APPROVE, REJECT
    comment: Optional[str] = None

# --- BACKGROUND TASKS ---
# Helper functions imported from api.deps

# --- PUBLIC ROUTES ---

# --- EHR / FHIR ENDPOINTS ---
@app.get("/ehr/patient/{patient_id}")
async def get_ehr_patient(patient_id: str, token: str = Depends(oauth2_scheme)):
    """Fetch patient demographics from EMR."""
    from integrations.fhir_connector import FHIRConnector
    fhir = FHIRConnector(base_url=settings.FHIR_BASE_URL)
    return await fhir.get_patient(patient_id)

@app.get("/ehr/history/{patient_id}")
async def get_ehr_history(patient_id: str, token: str = Depends(oauth2_scheme)):
    """Fetch patient clinical history from EMR."""
    from integrations.fhir_connector import FHIRConnector
    fhir = FHIRConnector(base_url=settings.FHIR_BASE_URL)
    conditions = await fhir.get_conditions(patient_id)
    meds = await fhir.get_medications(patient_id)
    return {"conditions": conditions, "medications": meds}

@app.post("/ehr/report")
async def push_ehr_report(report_data: dict, token: str = Depends(oauth2_scheme)):
    """Sync MEDAgent report back to Hospital EMR."""
    from integrations.fhir_connector import FHIRConnector
    fhir = FHIRConnector(base_url=settings.FHIR_BASE_URL)
    return await fhir.push_diagnostic_report(report_data)
@app.post("/consult")
async def consult(request: PatientRequest, background_tasks: BackgroundTasks, req: Request = None):
    try:
        # Rate limiting
        if req:
            allowed, retry_after = check_rate_limit(get_client_identifier(req))
            if not allowed:
                raise HTTPException(status_code=429, detail=f"Rate limit exceeded. Retry in {retry_after}s")
        request_id = str(uuid.uuid4())
        orch = get_orchestrator()
        t0 = time.perf_counter()
        if tracer:
            with tracer.start_as_current_span("consult") as span:
                span.set_attribute("request.id", request_id)
                span.set_attribute("user.id", request.patient_id)
                result = await orch.run(
                    request.symptoms, 
                    user_id=request.patient_id, 
                    image_path=request.image_path,
                    request_second_opinion=request.request_second_opinion,
                    interaction_mode=request.interaction_mode
                )
        else:
            result = await orch.run(
                request.symptoms, 
                user_id=request.patient_id, 
                image_path=request.image_path,
                request_second_opinion=request.request_second_opinion,
                interaction_mode=request.interaction_mode
            )
        t1 = time.perf_counter()
        result["request_id"] = request_id
        if "latency_ms" not in result:
            result["latency_ms"] = int((t1 - t0) * 1000)
        try:
            REQUEST_LATENCY.observe(result["latency_ms"])
            if result.get("model_used"):
                MODEL_USAGE.labels(result["model_used"]).inc()
            if result.get("critical_alert"):
                ESCALATIONS.inc()
        except Exception:
            pass
        
        if result.get("status") == "error":
            try:
                REQUEST_ERRORS.inc()
            except Exception:
                pass
            raise HTTPException(status_code=400, detail=result.get("final_response"))
            
        # Trigger background logic if priority is high
        if result.get("critical_alert"):
            background_tasks.add_task(send_health_alerts, request.patient_id, "EMERGENCY: High risk detected in your consultation.")
            
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Consultation failure: {e}")
        try:
            REQUEST_ERRORS.inc()
        except: pass
        raise HTTPException(status_code=500, detail=str(e))

# --- GENERATIVE ENGINE ROUTES ---
class EduRequest(BaseModel):
    topic: str
    audience: str = "patient"
    lang: str = "en"

class PlanRequest(BaseModel):
    diagnosis: str
    patient_profile: dict

@app.post("/generative/education")
async def generate_education(req: EduRequest, user: dict = Depends(get_current_user)):
    gen = get_generative_engine()
    content = gen.generate_educational_content(req.topic, req.audience, req.lang)
    return {"content": content}

@app.post("/generative/care-plan")
async def generate_care_plan(req: PlanRequest, user: dict = Depends(get_current_user)):
    gen = get_generative_engine()
    content = gen.generate_personalized_plan(req.patient_profile, req.diagnosis)
    return {"content": content}

@app.post("/generative/simulation")
async def generate_simulation(condition: str, user: dict = Depends(get_current_user)):
    if user["role"] != "doctor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only doctors can run simulations")
    gen = get_generative_engine()
    content = gen.generate_simulation_scenario(condition)
    return {"simulation": content}

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

# --- CLINICAL UTILITIES & GOVERNANCE ---
class LabInterpretRequest(BaseModel):
    lab_data: dict
    patient_id: Optional[str] = None

class SOAPRequest(BaseModel):
    interaction_id: int

class ABTestRequest(BaseModel):
    prompt_id: str
    prompt_a: str
    prompt_b: str
    test_cases: list

class RegistryReviewRequest(BaseModel):
    old_hash: str
    new_hash: str
    delta_report: str

class OverrideEscalationRequest(BaseModel):
    interaction_id: int
    override: bool
    rationale: Optional[str] = None

@app.post("/labs/interpret")
async def labs_interpret(req: LabInterpretRequest, user: dict = Depends(get_current_user)):
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage
    from agents.prompts.registry import PROMPT_REGISTRY
    entry = PROMPT_REGISTRY.get("MED-LOG-LAB-INT-001")
    if not entry:
        raise HTTPException(status_code=500, detail="Lab interpretation prompt missing")
    llm = ChatOpenAI(model=settings.OPENAI_MODEL, temperature=0.0, api_key=settings.OPENAI_API_KEY)
    prompt = entry.content.format(lab_data=req.lab_data, standard_ranges="standard")
    resp = llm.invoke([SystemMessage(content="You are a Clinical Pathology Interpreter."), HumanMessage(content=prompt)])
    return {"interpretation": resp.content}

@app.post("/docs/soap")
async def docs_soap(req: SOAPRequest, user: dict = Depends(get_current_user)):
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage
    from agents.prompts.registry import PROMPT_REGISTRY
    from database.models import Interaction
    pers = get_persistence()
    inter = pers.db.query(Interaction).filter(Interaction.id == req.interaction_id).first()
    if not inter:
        raise HTTPException(status_code=404, detail="Interaction not found")
    gov = get_governance()
    patient_story = gov.decrypt(inter.user_input_encrypted)
    diagnosis = gov.decrypt(inter.diagnosis_output_encrypted)
    entry = PROMPT_REGISTRY.get("MED-OP-SOAP-001")
    if not entry:
        raise HTTPException(status_code=500, detail="SOAP prompt missing")
    llm = ChatOpenAI(model=settings.OPENAI_MODEL, temperature=0.0, api_key=settings.OPENAI_API_KEY)
    prompt = entry.content.format(patient_story=patient_story, vitals_and_labs="N/A", diagnosis=diagnosis, next_steps="N/A")
    resp = llm.invoke([SystemMessage(content="Format strictly as SOAP note."), HumanMessage(content=prompt)])
    return {"soap": resp.content}

@app.post("/experiments/ab-test", dependencies=[Depends(check_admin_auth)])
async def ab_test(req: ABTestRequest):
    from agents.intelligence.ab_tester import ABTester
    tester = ABTester()
    result = tester.run_comparison(req.prompt_id, req.prompt_a, req.prompt_b, req.test_cases)
    return result

@app.post("/registry/review", dependencies=[Depends(check_admin_auth)])
async def registry_review(req: RegistryReviewRequest):
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage
    from agents.prompts.registry import PROMPT_REGISTRY
    entry = PROMPT_REGISTRY.get("MED-GOV-REGISTRY-001")
    if not entry:
        raise HTTPException(status_code=500, detail="Registry review prompt missing")
    llm = ChatOpenAI(model=settings.OPENAI_MODEL, temperature=0.0, api_key=settings.OPENAI_API_KEY)
    prompt = entry.content.format(old_hash=req.old_hash, new_hash=req.new_hash, delta_report=req.delta_report)
    resp = llm.invoke([SystemMessage(content="You are the Prompt Registry Governance Engine."), HumanMessage(content=prompt)])
    return {"review": resp.content}

@app.post("/admin/override-escalation", dependencies=[Depends(check_admin_auth)])
async def override_escalation(req: OverrideEscalationRequest):
    from database.models import Interaction, ReviewStatus
    pers = get_persistence()
    inter = pers.db.query(Interaction).filter(Interaction.id == req.interaction_id).first()
    if not inter:
        raise HTTPException(status_code=404, detail="Interaction not found")
    inter.requires_human_review = not req.override
    inter.review_status = ReviewStatus.APPROVED if req.override else ReviewStatus.FLAGGED
    inter.reviewer_comment = req.rationale
    pers.db.commit()
    return {"status": "ok", "requires_human_review": inter.requires_human_review}

class AuditExportRequest(BaseModel):
    interaction_id: Optional[int] = None

@app.post("/admin/audit-export", dependencies=[Depends(check_admin_auth)])
async def audit_export(req: AuditExportRequest):
    from database.models import Interaction, AuditLog
    pers = get_persistence()
    gov = get_governance()
    data = {}
    if req.interaction_id:
        inter = pers.db.query(Interaction).filter(Interaction.id == req.interaction_id).first()
        if not inter:
            raise HTTPException(status_code=404, detail="Interaction not found")
        data["interaction"] = {
            "id": inter.id,
            "timestamp": str(inter.timestamp),
            "audit_hash": inter.audit_hash,
            "model_used": inter.model_used,
            "prompt_version": inter.prompt_version,
            "risk_level": inter.risk_level,
            "confidence_score": inter.confidence_score,
        }
    # include recent audit logs summary
    logs = pers.db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(10).all()
    data["audit_logs"] = [{"time": str(l.timestamp), "actor": l.actor_id, "action": l.action, "status": l.status} for l in logs]
    payload = json.dumps(data, indent=2)
    try:
        sig = gov.sign_evidence(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"evidence": data, "signature": sig}

# --- ANALYTICS ROUTES ---
class SymptomRequest(BaseModel):
    symptom: str
    severity: int
    notes: Optional[str] = None

class MedicationRequest(BaseModel):
    name: str
    dosage: str
    frequency: str

@app.post("/analytics/symptoms")
async def log_symptom(req: SymptomRequest, user: dict = Depends(get_current_user)):
    pers = get_persistence()
    success = pers.log_symptom(user["sub"], req.symptom, req.severity, req.notes)
    if not success: raise HTTPException(status_code=500, detail="Failed to log symptom")
    return {"status": "success"}

@app.get("/analytics/symptoms")
async def get_symptoms(user: dict = Depends(get_current_user)):
    pers = get_persistence()
    return pers.get_symptoms(user["sub"])

@app.post("/analytics/medications")
async def log_medication(req: MedicationRequest, user: dict = Depends(get_current_user)):
    pers = get_persistence()
    success = pers.log_medication(user["sub"], req.name, req.dosage, req.frequency)
    if not success: raise HTTPException(status_code=500, detail="Failed to log medication")
    return {"status": "success"}

@app.get("/analytics/medications")
async def get_medications(user: dict = Depends(get_current_user)):
    pers = get_persistence()
    return pers.get_medications(user["sub"])

@app.get("/analytics/export-pdf")
async def export_report(user: dict = Depends(get_current_user)):
    pers = get_persistence()
    exporter = get_export_agent()
    gov = get_governance()
    
    # Fetch patient profile
    db = pers._get_db()
    try:
        from database.models import PatientProfile, Interaction
        p = db.query(PatientProfile).filter(PatientProfile.id == user["sub"]).first()
        if not p: raise HTTPException(status_code=404, detail="Profile not found")
        
        profile_dict = {
            "id": p.id,
            "age": p.age,
            "gender": p.gender
        }
        
        # Fetch last 20 interactions
        items = db.query(Interaction).filter(Interaction.session_id.in_(
            db.query(UserSession.id).filter(UserSession.user_id == user["sub"])
        )).order_by(Interaction.timestamp.desc()).limit(20).all()
        
        interactions = []
        for i in items:
            interactions.append({
                "timestamp": i.timestamp.isoformat(),
                "diagnosis": gov.decrypt(i.diagnosis_output_encrypted),
                "audit_hash": i.audit_hash
            })
            
        file_path = f"export_{user['sub']}.pdf"
        success = exporter.generate_patient_summary_pdf(profile_dict, interactions, file_path)
        
        if success:
            from fastapi.responses import FileResponse
            return FileResponse(file_path, media_type="application/pdf", filename="MedAgent_Report.pdf")
        else:
            raise HTTPException(status_code=500, detail="PDF generation failed")
    finally:
        db.close()

@app.get("/health")
async def health_check():
    """System Health and Maintenance Dashboard."""
    from agents.orchestrator import MedAgentOrchestrator
    try:
        # Check database connectivity
        from database.models import get_db
        db = next(get_db())
        db.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        db_status = f"unhealthy: {e}"
    
    return {
        "status": "operational",
        "version": "1.2.0-maintenance",
        "database": db_status,
        "agents": {
            "orchestrator": "initialized",
            "optimization": "lazy_loading_enabled",
            "correction_loop": "active"
        },
        "performance": {
            "startup_mode": "asynchronous_optimized"
        }
    }

class TTSRequest(BaseModel):
    text: str

@app.post("/system/tts")
async def text_to_speech(req: TTSRequest, user: dict = Depends(get_current_user)):
    """Generate audio for medical response using OpenAI Speech API."""
    import openai
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy", # or 'nova' for different tones
            input=req.text[:4000] # OpenAI TTS limit
        )
        # Return binary audio stream
        from fastapi.responses import Response
        return Response(content=response.content, media_type="audio/mpeg")
    except Exception as e:
        logger.error(f"TTS failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- PEDIATRIC / CHILD-FRIENDLY ENDPOINTS ---
@app.post("/pediatric/explain")
async def pediatric_explain(clinical_finding: str, age: int = 8, token: str = Depends(oauth2_scheme)):
    """Translate clinical results into Theo's child-friendly explanation."""
    from agents.pediatric_agent import PediatricAgent
    agent = PediatricAgent()
    return agent.process_explanation(clinical_finding, age)

@app.post("/pediatric/visualize")
async def pediatric_visualize(prompt: str, token: str = Depends(oauth2_scheme)):
    """Generate a Theo-style visual aid for the child."""
    # Placeholder for DALL-E/StableDiffusion integration
    return {"visual_prompt": prompt, "status": "Ready for generation"}

# --- CLINICAL GOVERNANCE & AUDIT ENDPOINTS ---
@app.get("/governance/audit-logs")
async def get_audit_logs(limit: int = 50, token: str = Depends(oauth2_scheme)):
    """Retrieve high-fidelity AI audit logs for clinical compliance."""
    from database.models import AIAuditLog, SessionLocal
    with SessionLocal() as db:
        logs = db.query(AIAuditLog).order_by(AIAuditLog.timestamp.desc()).limit(limit).all()
        return logs

@app.post("/governance/review/approve")
async def approve_case(interaction_id: int, comment: str, token: str = Depends(oauth2_scheme)):
    """Doctor approval for a high-risk AI suggestion."""
    from database.models import Interaction, SessionLocal, ReviewStatus
    with SessionLocal() as db:
        interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
        if interaction:
            interaction.review_status = ReviewStatus.APPROVED
            interaction.reviewer_comment = comment
            db.commit()
            return {"status": "Case approved"}
        raise HTTPException(status_code=404, detail="Interaction not found")

@app.get("/governance/compliance/export")
async def export_compliance_report(format: str = "fhir", token: str = Depends(oauth2_scheme)):
    """Export clinical logs in regulated formats (FHIR AuditEvent)."""
    from utils.audit_logger import AuditLogger
    if format == "fhir":
        return AuditLogger.export_fhir_audit_event(log_id=0) # Placeholder for batch export
    return {"error": "Unsupported format"}
