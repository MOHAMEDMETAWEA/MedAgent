
import uuid
import logging
from fastapi import HTTPException, Depends, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from jose import jwt
from pathlib import Path

from agents.persistence_agent import PersistenceAgent
from agents.governance_agent import GovernanceAgent
from agents.authentication_agent import AuthenticationAgent
from agents.self_improvement_agent import SelfImprovementAgent
from agents.developer_agent import DeveloperControlAgent
from agents.human_review_agent import HumanReviewAgent
from agents.medication_agent import MedicationAgent
from agents.calendar_agent import CalendarAgent
from agents.generative_engine_agent import GenerativeEngineAgent
from agents.report_agent import ReportAgent
from agents.audit_agent import AuditAgent
from agents.export_agent import ExportAgent
from agents.orchestrator import MedAgentOrchestrator
from agents.verification_agent import VerificationAgent
from agents.interop.fhir_hl7_builder import InteropBuilder
from config import settings

logger = logging.getLogger(__name__)

# API Key Auth
API_KEY_NAME = "X-Admin-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def check_admin_auth(api_key: str = Depends(api_key_header)):
    expected_key = settings.ADMIN_API_KEY
    if not expected_key:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server misconfigured: ADMIN_API_KEY missing")
    if api_key != expected_key:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Auth Failed")
    return True

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

async def verify_clerk_token(token: str):
    if not settings.CLERK_SECRET_KEY: return None
    try:
        payload = jwt.get_unverified_claims(token)
        return payload
    except Exception as e:
        logger.error(f"Clerk token verification failed: {e}")
        return None

# Singletons
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
_generative_engine = None
_interop_builder = None
_audit_agent = None
_export_agent = None

def get_persistence():
    global _persistence
    if _persistence is None: _persistence = PersistenceAgent()
    return _persistence

def get_governance():
    global _governance
    if _governance is None: _governance = GovernanceAgent()
    return _governance

def get_orchestrator():
    global _orchestrator
    if _orchestrator is None: _orchestrator = MedAgentOrchestrator()
    return _orchestrator

def get_auth_agent():
    global _auth_agent
    if _auth_agent is None: _auth_agent = AuthenticationAgent()
    return _auth_agent

# Add others as needed
def get_verification_agent():
    global _verification_agent
    if _verification_agent is None: _verification_agent = VerificationAgent()
    return _verification_agent

def get_improver():
    global _improver
    if _improver is None: _improver = SelfImprovementAgent()
    return _improver

def get_developer_agent():
    global _developer_agent
    if _developer_agent is None: _developer_agent = DeveloperControlAgent()
    return _developer_agent

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

def get_generative_engine():
    global _generative_engine
    if _generative_engine is None: _generative_engine = GenerativeEngineAgent()
    return _generative_engine

def get_interop_builder():
    global _interop_builder
    if _interop_builder is None: _interop_builder = InteropBuilder()
    return _interop_builder

def get_audit_agent():
    global _audit_agent
    if _audit_agent is None: _audit_agent = AuditAgent()
    return _audit_agent

def get_export_agent():
    global _export_agent
    if _export_agent is None: _export_agent = ExportAgent()
    return _export_agent

async def get_current_user(token: str = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    
    gov = get_governance()
    payload = gov.verify_token(token)
    if payload: return payload
    
    clerk_payload = await verify_clerk_token(token)
    if clerk_payload:
        pers = get_persistence()
        clerk_id = clerk_payload.get("sub")
        email = clerk_payload.get("email") or clerk_payload.get("email_address")
        user = pers.get_user_by_clerk_id(clerk_id)
        if not user:
            username = clerk_payload.get("username") or f"user_{clerk_id[:8]}"
            full_name = clerk_payload.get("name") or username
            user_id = await pers.register_user(
                username=username, email=email or f"{clerk_id}@clerk.local",
                phone="000", password=str(uuid.uuid4()), full_name=full_name, clerk_id=clerk_id
            )
            return {"sub": user_id, "role": "patient", "name": full_name}
        return {"sub": user.id, "role": user.role.value if hasattr(user.role, 'value') else str(user.role), "name": user.username}
    
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
