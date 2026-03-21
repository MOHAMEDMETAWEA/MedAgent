"""
FastAPI Backend for MedAgent - Enhanced Command Center.
Includes Admin Routes, System Health, and Governance Controls.
Updated for Feedback, Review, and Medical Image Analysis.
"""

import sys

print("DEBUG: Importing api.main", file=sys.stderr)
import datetime
import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, List, Optional

import bcrypt

# Monkeypatch bcrypt for passlib compatibility in newer versions
if not hasattr(bcrypt, "__about__"):

    class BcryptAbout:
        __version__ = getattr(bcrypt, "__version__", "unknown")

    bcrypt.__about__ = BcryptAbout()


_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import time

import httpx
from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from prometheus_client import (CONTENT_TYPE_LATEST, Counter, Gauge, Histogram,
                               generate_latest)
from pydantic import BaseModel

from agents.orchestrator import MedAgentOrchestrator
from agents.persistence_agent import PersistenceAgent
from config import settings
from utils.rate_limit import check_rate_limit, get_client_identifier
from utils.safety import sanitize_input, validate_medical_input

# Hospital Performance Metrics
HOSPITAL_LOAD = Gauge(
    "medagent_hospital_concurrent_users", "Number of concurrent clinical sessions"
)
SAFETY_INCIDENTS = Counter(
    "medagent_safety_blocks_total", "Total count of unsafe advice blocks"
)
EHR_SYNC_LATENCY = Histogram(
    "medagent_ehr_sync_seconds", "Latency of FHIR data synchronization"
)
CLINICAL_ERROR_RATE = Counter(
    "medagent_clinical_errors_total", "Total clinical exceptions tracked"
)

from fastapi.responses import Response
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (ConsoleSpanExporter,
                                            SimpleSpanProcessor)

logger = logging.getLogger(__name__)

from api.deps import (check_admin_auth, get_audit_agent, get_auth_agent,
                      get_calendar_agent, get_current_user,
                      get_developer_agent, get_export_agent,
                      get_generative_engine, get_governance, get_improver,
                      get_interop_builder, get_medication_agent,
                      get_orchestrator, get_persistence, get_report_agent,
                      get_review_agent, get_verification_agent, oauth2_scheme)
from api.routes import (analytics, auth, clinical, docs, ehr, feedback,
                        governance, imaging, learning, patient, pediatric,
                        system)


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


app = FastAPI(
    title="MedAgent Global System", version="5.3.0-PRODUCTION", lifespan=lifespan
)

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
app.include_router(docs.router)
app.include_router(analytics.router)
app.include_router(pediatric.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Observability (Retained in main for global context)
REQUEST_LATENCY = Histogram(
    "medagent_request_latency_ms",
    "Request latency in ms",
    buckets=[50, 100, 200, 500, 1000, 2000, 5000],
)
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

    return JSONResponse(
        status_code=503, content={"status": "not_ready", "version": "5.3.0"}
    )


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
                detail=f"Unsupported format. Allowed: {', '.join(ALLOWED_IMAGE_FORMATS)}",
            )

        # Read file content
        content = await file.read()

        # Validate file size
        if len(content) > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=400, detail="File too large. Maximum 20MB allowed."
            )

        file_name = f"{uuid.uuid4()}.{file_ext}"
        file_path = UPLOAD_DIR / file_name

        with open(file_path, "wb") as f:
            f.write(content)

        return {
            "image_path": str(file_path),
            "filename": file.filename,
            "size_bytes": len(content),
            "format": file_ext,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/system/capabilities")
async def get_capabilities():
    """List all active agents and generative capabilities (Bilingual)."""
    return {
        "agents": [
            {
                "name": "Triage Agent / عميل الفرز",
                "role": "Analyzes symptoms and severity / يحلل الأعراض والخطورة",
            },
            {
                "name": "Knowledge Agent / عميل المعرفة",
                "role": "Retrieves medical literature via RAG / يسترجع الأدبيات الطبية",
            },
            {
                "name": "Reasoning Agent / عميل التفكير",
                "role": "Performs differential analysis / يقوم بالتحليل التفريقي",
            },
            {
                "name": "Safety Agent / عميل السلامة",
                "role": "Check for errors and safety / يتحقق من الأخطاء والسلامة",
            },
            {
                "name": "Validation Agent / عميل التحقق",
                "role": "Verifies medical accuracy / يتحقق من الدقة الطبية",
            },
            {
                "name": "Vision Analysis Agent / عميل تحليل الصور",
                "role": "Analyzes medical images (X-ray, Rashes, etc.) / يحلل الصور الطبية (الأشعة، الأمراض الجلدية، إلخ)",
            },
            {
                "name": "Patient Agent / عميل المريض",
                "role": "Manages patient profile and history / يدير ملف المريض وتاريخه",
            },
            {
                "name": "Report Agent / عميل التقارير",
                "role": "Generates medical reports / ينشئ التقارير الطبية",
            },
            {
                "name": "Calendar Agent / عميل التقويم",
                "role": "Manages appointments / يدير المواعيد",
            },
            {
                "name": "Supervisor Agent / عميل الإشراف",
                "role": "Monitors system health / يراقب صحة النظام",
            },
            {
                "name": "Self-Improvement Agent / عميل التحسين الذاتي",
                "role": "Learns from feedback / يتعلم من التعليقات",
            },
            {
                "name": "Developer Control Agent / عميل التحكم المطور",
                "role": "System management for devs / إدارة النظام للمطورين",
            },
            {
                "name": "Medication Agent / عميل الأدوية",
                "role": "Tracks dosages and reminders / يتتبع الجرعات والتذكيرات",
            },
            {
                "name": "Second Opinion Agent / عميل الرأي الثاني",
                "role": "Independent diagnostic audit / تدقيق تشخيصي مستقل",
            },
            {
                "name": "Human Review Agent / عميل المراجعة البشرية",
                "role": "Clinician-in-the-loop audit / مراجعة الطبيب المختص",
            },
            {
                "name": "Verification Agent / عميل التحقق",
                "role": "Validates doctor licenses / يتحقق من تراخيص الأطباء",
            },
            {
                "name": "Authentication Agent / عميل الهوية",
                "role": "Secure JWT management / إدارة الهوية الآمنة",
            },
            {
                "name": "Persistence Agent / عميل الاستمرارية",
                "role": "Manages medical memory graph / يدير سجل الذاكرة الطبية",
            },
            {
                "name": "Governance Agent / عميل الحوكمة",
                "role": "AES-256 encryption authority / سلطة التشفير والحوكمة",
            },
            {
                "name": "Evolution Agent / عميل التطور",
                "role": "Autonomous medical model fine-tuning / التطوير الذاتي للنماذج الطبية",
            },
        ],
        "capabilities": [
            {
                "id": "AUTONOMOUS_LEARNING",
                "label": "Autonomous Model Evolution / التطور الذاتي للنماذج",
                "generative": True,
            },
            {
                "id": "EHR_INTEROPERABILITY",
                "label": "EHR/FHIR Integration / التكامل مع السجلات الإلكترونية",
                "generative": False,
            },
            {
                "id": "IMAGE_ANALYSIS",
                "label": "Medical Image Analysis / تحليل الصور الطبية",
                "generative": True,
            },
            {
                "id": "GENERATE_REPORT",
                "label": "Generate Report / إنشاء تقرير",
                "generative": True,
            },
            {
                "id": "GENERATE_RECOMMENDATION",
                "label": "Generate Recommendation / إنشاء توصية",
                "generative": True,
            },
            {
                "id": "BOOK_APPOINTMENT",
                "label": "Book Appointment / حجز موعد",
                "generative": False,
            },
            {
                "id": "RETRIEVE_HISTORY",
                "label": "Retrieval History / استرجاع السجل",
                "generative": False,
            },
            {
                "id": "DATA_EXPORT",
                "label": "Data Export / تصدير البيانات",
                "generative": False,
            },
            {
                "id": "MEMORY_GRAPH",
                "label": "Memory Graph / سجل الذاكرة",
                "generative": False,
            },
            {
                "id": "RAG_INSIGHTS",
                "label": "RAG Context / سياق المعرفة Retrieval Augmented Generation",
                "generative": False,
            },
            {
                "id": "TREE_OF_THOUGHT",
                "label": "Clinical Reasoning (ToT) / التفكير السريري",
                "generative": True,
            },
        ],
    }


class LabsInterpretRequest(BaseModel):
    lab_data: dict


@app.post("/labs/interpret")
async def labs_interpret(
    req: LabsInterpretRequest, user: dict = Depends(get_current_user)
):
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_openai import ChatOpenAI

    from agents.prompts.registry import PROMPT_REGISTRY

    entry = PROMPT_REGISTRY.get("MED-LOG-LAB-INT-001")
    if not entry:
        raise HTTPException(status_code=500, detail="Lab interpretation prompt missing")
    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL, temperature=0.0, api_key=settings.OPENAI_API_KEY
    )
    prompt = entry.content.format(lab_data=req.lab_data, standard_ranges="standard")
    resp = llm.invoke(
        [
            SystemMessage(content="You are a Clinical Pathology Interpreter."),
            HumanMessage(content=prompt),
        ]
    )
    return {"interpretation": resp.content}


class SOAPRequest(BaseModel):
    interaction_id: int


@app.post("/docs/soap")
async def docs_soap(req: SOAPRequest, user: dict = Depends(get_current_user)):
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_openai import ChatOpenAI

    from agents.prompts.registry import PROMPT_REGISTRY
    from database.models import Interaction

    pers = get_persistence()
    inter = (
        pers.db.query(Interaction).filter(Interaction.id == req.interaction_id).first()
    )
    if not inter:
        raise HTTPException(status_code=404, detail="Interaction not found")
    gov = get_governance()
    patient_story = gov.decrypt(inter.user_input_encrypted)
    diagnosis = gov.decrypt(inter.diagnosis_output_encrypted)
    entry = PROMPT_REGISTRY.get("MED-OP-SOAP-001")
    if not entry:
        raise HTTPException(status_code=500, detail="SOAP prompt missing")
    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL, temperature=0.0, api_key=settings.OPENAI_API_KEY
    )
    prompt = entry.content.format(
        patient_story=patient_story,
        vitals_and_labs="N/A",
        diagnosis=diagnosis,
        next_steps="N/A",
    )
    resp = llm.invoke(
        [
            SystemMessage(content="Format strictly as SOAP note."),
            HumanMessage(content=prompt),
        ]
    )
    return {"soap": resp.content}


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
            voice="alloy",  # or 'nova' for different tones
            input=req.text[:4000],  # OpenAI TTS limit
        )
        # Return binary audio stream
        from fastapi.responses import Response

        return Response(content=response.content, media_type="audio/mpeg")
    except Exception as e:
        logger.error(f"TTS failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
