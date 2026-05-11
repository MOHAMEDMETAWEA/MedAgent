import datetime
import hashlib
import json
import logging
import os
import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.audit_agent import AuditAgent
from agents.governance_agent import GovernanceAgent
from config import settings
from database.models import (AsyncSessionLocal, Feedback, Interaction,
                             MedicalCase, MedicalImage, MedicalReport,
                             MedicationRecord, MemoryEdge, MemoryNode,
                             PatientProfile, SessionLocal, SymptomLog,
                             SystemLog, UserAccount, UserAction, UserActivity,
                             UserRole, UserSession)

logger = logging.getLogger(__name__)


class PersistenceAgent:
    """
    Agent responsible for saving interactions and logs to the database.
    Production-grade: Fully Asynchronous, Encrypted, and Audited.
    """

    def __init__(self):
        self.governance = GovernanceAgent()
        self.audit = AuditAgent()
        self.db = SessionLocal()  # Legacy sync support for older routes

    async def create_session(
        self, user_id: str = "guest", mode: str = "patient"
    ) -> str:
        """Start a new tracking session (Async)."""
        session_id = str(uuid.uuid4())
        async with AsyncSessionLocal() as db:
            try:
                new_session = UserSession(
                    id=session_id,
                    user_id=user_id,
                    status="active",
                    interaction_mode=mode,
                )
                db.add(new_session)
                await db.commit()
                return session_id
            except Exception as e:
                logger.error(f"Failed to create session: {e}")
                await db.rollback()
                return session_id

    async def process(self, state: dict) -> dict:
        """Standardized agent entry point for LangGraph (Async)."""
        logger.info("--- PERSISTENCE AGENT: SAVING INTERACTION ---")
        session_id = state.get("session_id")
        user_input = ""
        messages = state.get("messages", [])
        if messages:
            last_msg = messages[-1]
            user_input = getattr(last_msg, "content", "")

        if session_id and user_input:
            await self.save_interaction(
                session_id=session_id,
                user_input=user_input,
                result=state,
                case_id=state.get("conversation_state", {}).get("active_case_id"),
            )
        return state

    async def save_interaction(
        self, session_id: str, user_input: str, result: dict, case_id: str = None
    ):
        """High-level interaction save (Async)."""
        async with AsyncSessionLocal() as db:
            return await self._save_interaction_db(
                db, session_id, user_input, result, case_id
            )

    async def _save_interaction_db(
        self,
        db: AsyncSession,
        session_id: str,
        user_input: str,
        result: dict,
        case_id: str = None,
    ):
        """Internal helper to save interaction using provided async DB session."""
        try:
            enc_input = self.governance.encrypt(user_input)
            enc_diagnosis = self.governance.encrypt(
                result.get("preliminary_diagnosis", "")
            )
            enc_response = self.governance.encrypt(result.get("final_response", ""))

            prompt_version = result.get("prompt_version")
            model_used = result.get(
                "model_used", getattr(settings, "OPENAI_MODEL", None)
            )

            stmt = (
                select(Interaction)
                .filter(Interaction.session_id == session_id)
                .order_by(Interaction.timestamp.desc())
            )
            exec_res = await db.execute(stmt)
            prev_interaction = exec_res.scalars().first()
            prev_hash = prev_interaction.audit_hash if prev_interaction else "GENESIS"

            base_str = f"{session_id}|{enc_input}|{enc_response}|{model_used or ''}|{prompt_version or ''}|{prev_hash}|{datetime.datetime.utcnow().isoformat()}"
            audit_hash = hashlib.sha256(base_str.encode("utf-8")).hexdigest()

            interaction = Interaction(
                session_id=session_id,
                case_id=case_id,
                user_input_encrypted=enc_input,
                diagnosis_output_encrypted=enc_diagnosis,
                final_response_encrypted=enc_response,
                metadata_json=result.get("patient_info", {}),
                safety_flags={"critical_alert": result.get("critical_alert", False)},
                prompt_version=prompt_version,
                model_used=model_used,
                secondary_model=result.get("secondary_model"),
                confidence_score=result.get("confidence_score"),
                risk_level=result.get("risk_level"),
                audit_hash=audit_hash,
                previous_audit_hash=prev_hash,
                latency_ms=result.get("latency_ms", 0),
            )
            db.add(interaction)
            await db.commit()
            return interaction.id
        except Exception as e:
            logger.error(f"Failed to save interaction: {e}")
            await db.rollback()
            return None

    async def log_system_event(
        self,
        level: str,
        component: str,
        message: str,
        details: dict = None,
        session_id: str = None,
    ):
        """Log a system event or error (Async)."""
        async with AsyncSessionLocal() as db:
            try:
                redacted_message = message
                redacted_details = details or {}
                try:
                    from agents.safety.privacy_audit import PrivacyAuditLayer

                    pal = PrivacyAuditLayer()
                    redacted_message = pal.redact_phi(message) if message else message
                    if redacted_details:
                        redacted_details = {
                            "_redacted": pal.redact_phi(str(redacted_details))
                        }
                except Exception:
                    pass
                log_entry = SystemLog(
                    level=level,
                    component=component,
                    message=redacted_message,
                    details=redacted_details,
                    session_id=session_id,
                )
                db.add(log_entry)
                await db.commit()
            except Exception as e:
                logger.error(f"DB Logging failed: {e}")
                await db.rollback()

    async def get_user_history(self, user_id: str, limit: int = 10):
        """Retrieve past sessions for a user (Async)."""
        async with AsyncSessionLocal() as db:
            try:
                stmt = (
                    select(UserSession)
                    .filter(UserSession.user_id == user_id)
                    .order_by(UserSession.start_time.desc())
                    .limit(limit)
                )
                res = await db.execute(stmt)
                return res.scalars().all()
            except Exception as e:
                logger.error(f"Failed to retrieve history: {e}")
                return []

    async def get_session_history(self, session_id: str, limit: int = 20):
        """Retrieve all interactions for a specific session code (Async)."""
        async with AsyncSessionLocal() as db:
            try:
                stmt = (
                    select(Interaction)
                    .filter(Interaction.session_id == session_id)
                    .order_by(Interaction.timestamp.asc())  # Chronicle order
                    .limit(limit)
                )
                res = await db.execute(stmt)
                interactions = res.scalars().all()

                history = []
                for i in interactions:
                    try:
                        u_in = self.governance.decrypt(i.user_input_encrypted)
                        ai_out = self.governance.decrypt(i.final_response_encrypted)
                        history.append({"user": u_in, "ai": ai_out})
                    except Exception as e:
                        logger.error(
                            f"History decryption failed for interaction {i.id}: {e}"
                        )

                return history
            except Exception as e:
                logger.error(f"Failed to retrieve session history: {e}")
                return []

    async def get_long_term_memory(self, user_id: str, limit_sessions: int = 3):
        """Fetch and format past interactions for LLM context (Async)."""
        async with AsyncSessionLocal() as db:
            try:
                sessions_stmt = (
                    select(UserSession)
                    .filter(UserSession.user_id == user_id)
                    .order_by(UserSession.start_time.desc())
                    .limit(limit_sessions)
                )
                sessions_res = await db.execute(sessions_stmt)
                sessions = sessions_res.scalars().all()

                memory_text = ""
                for s in sessions:
                    int_stmt = (
                        select(Interaction)
                        .filter(Interaction.session_id == s.id)
                        .order_by(Interaction.timestamp.asc())
                    )
                    int_res = await db.execute(int_stmt)
                    interactions = int_res.scalars().all()
                    if not interactions:
                        continue
                    memory_text += f"\
--- PAST SESSION: {s.id} ({s.start_time.strftime('%Y-%m-%d')}) ---\
"
                    for i in interactions:
                        u_in = self.governance.decrypt(i.user_input_encrypted)
                        diag = self.governance.decrypt(i.diagnosis_output_encrypted)
                        memory_text += f"User: {u_in}\
AI Diagnosis: {diag}\
"
                return (
                    memory_text if memory_text else "No previous medical history found."
                )
            except Exception as e:
                logger.error(f"Failed to fetch long term memory: {e}")
                return "Error loading history."

    # --- Patient Profile & Reporting Methods ---

    async def get_patient_profile(self, user_id: str):
        """Retrieve decrypted patient profile (Async)."""
        async with AsyncSessionLocal() as db:
            try:
                stmt = select(PatientProfile).filter(PatientProfile.id == user_id)
                res = await db.execute(stmt)
                profile = res.scalars().first()
                if not profile:
                    return None

                decrypted_name = (
                    self.governance.decrypt(profile.name_encrypted)
                    if profile.name_encrypted
                    else ""
                )
                decrypted_history = (
                    self.governance.decrypt(profile.medical_history_encrypted)
                    if profile.medical_history_encrypted
                    else ""
                )

                return {
                    "id": profile.id,
                    "name": decrypted_name,
                    "age": profile.age,
                    "gender": profile.gender,
                    "medical_history": decrypted_history,
                    "created_at": profile.created_at,
                }
            except Exception as e:
                logger.error(f"Failed to fetch patient profile: {e}")
                return None

    async def upsert_patient_profile(
        self, user_id: str, name: str, age: int, gender: str, history_json: str
    ):
        """Create or Update patient profile securely (Async)."""
        async with AsyncSessionLocal() as db:
            return await self._upsert_patient_profile_db(
                db, user_id, name, age, gender, history_json
            )

    async def _upsert_patient_profile_db(
        self,
        db: AsyncSession,
        user_id: str,
        name: str,
        age: int,
        gender: str,
        history_json: str,
    ):
        """Internal helper for patient profile upsert (Async)."""
        try:
            stmt = select(PatientProfile).filter(PatientProfile.id == user_id)
            res = await db.execute(stmt)
            profile = res.scalars().first()

            enc_name = self.governance.encrypt(name)
            enc_history = self.governance.encrypt(history_json)

            if not profile:
                profile = PatientProfile(
                    id=user_id,
                    name_encrypted=enc_name,
                    age=age,
                    gender=gender,
                    medical_history_encrypted=enc_history,
                )
                db.add(profile)
            else:
                profile.name_encrypted = enc_name
                profile.age = age
                profile.gender = gender
                profile.medical_history_encrypted = enc_history

            await db.commit()
            self.audit.log_change(
                user_id,
                "SYSTEM",
                "UPDATE_PROFILE",
                f"Profile#{user_id}",
                details={"age": age, "gender": gender},
            )
            return True
        except Exception as e:
            logger.error(f"Failed to upsert profile: {e}")
            await db.rollback()
            return False

    async def save_medical_report(
        self,
        session_id: str,
        patient_id: str,
        content_json: str,
        report_type: str = "comprehensive",
        lang: str = "en",
        status: str = "pending",
    ):
        """Save a new version of a generated medical report (Async)."""
        async with AsyncSessionLocal() as db:
            try:
                prof_stmt = select(PatientProfile).filter(
                    PatientProfile.id == patient_id
                )
                prof_res = await db.execute(prof_stmt)
                if not prof_res.scalars().first():
                    await self._upsert_patient_profile_db(
                        db, patient_id, "Guest Patient", 0, "Unknown", "{}"
                    )

                enc_content = self.governance.encrypt(content_json)
                last_stmt = (
                    select(MedicalReport)
                    .filter(MedicalReport.patient_id == patient_id)
                    .order_by(MedicalReport.version.desc())
                )
                last_res = await db.execute(last_stmt)
                last_report = last_res.scalars().first()

                new_version = (last_report.version + 1) if last_report else 1
                new_report = MedicalReport(
                    patient_id=patient_id,
                    session_id=session_id,
                    report_content_encrypted=enc_content,
                    report_type=report_type,
                    language=lang,
                    version=new_version,
                    status=status,
                )
                db.add(new_report)
                await db.commit()
                return new_report.id
            except Exception as e:
                logger.error(f"Failed to save medical report: {e}")
                await db.rollback()
                return None

    async def save_medical_image(
        self,
        session_id: str,
        image_path: str,
        findings: dict,
        patient_id: str = None,
        case_id: str = None,
    ):
        """Save medical image metadata (Async)."""
        async with AsyncSessionLocal() as db:
            try:
                enc_path = self.governance.encrypt(image_path)
                enc_findings = self.governance.encrypt(
                    str(findings.get("visual_findings", ""))
                )

                new_image = MedicalImage(
                    session_id=session_id,
                    patient_id=patient_id,
                    case_id=case_id,
                    image_path_encrypted=enc_path,
                    original_filename=os.path.basename(image_path),
                    visual_findings_encrypted=enc_findings,
                    possible_conditions_json=findings.get("possible_conditions", []),
                    confidence_score=int(findings.get("confidence", 0) * 100),
                    severity_level=findings.get("severity_level", "low"),
                    requires_human_review=findings.get("requires_human_review", False),
                )
                db.add(new_image)
                await db.commit()
                return new_image.id
            except Exception as e:
                logger.error(f"Failed to save medical image: {e}")
                await db.rollback()
                return None

    async def get_session_images(self, session_id: str):
        """Retrieve all images for a session, decrypted (Async)."""
        async with AsyncSessionLocal() as db:
            try:
                stmt = select(MedicalImage).filter(
                    MedicalImage.session_id == session_id
                )
                res = await db.execute(stmt)
                images = res.scalars().all()
                result = []
                for img in images:
                    result.append(
                        {
                            "id": img.id,
                            "timestamp": img.timestamp,
                            "image_path": self.governance.decrypt(
                                img.image_path_encrypted
                            ),
                            "visual_findings": self.governance.decrypt(
                                img.visual_findings_encrypted
                            ),
                            "confidence": img.confidence_score / 100.0,
                            "severity": img.severity_level,
                        }
                    )
                return result
            except Exception as e:
                logger.error(f"Failed to fetch session images: {e}")
                return []

    async def save_user_action(
        self,
        session_id: str,
        action_type: str,
        element_id: str,
        details: dict = None,
        audit_tag: str = "UX",
    ):
        """Save a granular user UI action (Async)."""
        async with AsyncSessionLocal() as db:
            try:
                action = UserAction(
                    session_id=session_id,
                    action_type=action_type,
                    element_id=element_id,
                    details=details or {},
                    audit_tag=audit_tag,
                )
                db.add(action)
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"Failed to save user action: {e}")
                await db.rollback()
                return False

    # --- IDENTITY & AUTHENTICATION ---

    async def register_user(
        self,
        username: str,
        email: str,
        phone: str,
        password: str,
        full_name: str,
        role: str = "patient",
        gender: str = None,
        age: int = None,
        country: str = None,
        meta: dict = None,
        clerk_id: str = None,
    ):
        """Create a new user account securely (Async)."""
        async with AsyncSessionLocal() as db:
            try:
                user_id = str(uuid.uuid4())
                hashed_pwd = self.governance.hash_password(password)
                enc_name = self.governance.encrypt(full_name)
                enc_meta = self.governance.encrypt(str(meta or {}))

                try:
                    user_role = UserRole(role)
                except ValueError:
                    user_role = UserRole.PATIENT

                user = UserAccount(
                    id=user_id,
                    username=username,
                    email=email,
                    phone=phone,
                    full_name_encrypted=enc_name,
                    password_hash=hashed_pwd,
                    role=user_role,
                    gender=gender,
                    age=age,
                    country=country,
                    interaction_mode=(
                        role if role in ["patient", "doctor"] else "patient"
                    ),
                    profile_metadata_encrypted=enc_meta,
                    clerk_id=clerk_id,
                )
                db.add(user)
                await db.commit()

                self.audit.log_change(
                    user_id,
                    role,
                    "REGISTER_USER",
                    f"User#{user_id}",
                    details={"username": username, "email": email},
                )
                await self._upsert_patient_profile_db(
                    db, user_id, full_name, age or 0, gender or "Unknown", "{}"
                )
                return user_id
            except Exception as e:
                logger.error(f"Registration failed: {e}")
                await db.rollback()
                return None

    async def update_interaction_mode(self, user_id: str, mode: str):
        """Update user interaction mode (Async)."""
        async with AsyncSessionLocal() as db:
            try:
                stmt = select(UserAccount).filter(UserAccount.id == user_id)
                res = await db.execute(stmt)
                user = res.scalars().first()
                if user:
                    user.interaction_mode = mode
                    await db.commit()
                    return True
                return False
            except Exception as e:
                logger.error(f"Failed to update interaction mode: {e}")
                await db.rollback()
                return False

    async def verify_doctor(
        self, user_id: str, license_number: str, specialization: str
    ):
        """Verify doctor credentials (Async)."""
        async with AsyncSessionLocal() as db:
            try:
                stmt = select(UserAccount).filter(UserAccount.id == user_id)
                res = await db.execute(stmt)
                user = res.scalars().first()
                if user and user.role == UserRole.DOCTOR:
                    user.license_number = license_number
                    user.specialization = specialization
                    user.doctor_verified = True
                    await db.commit()
                    return True
                return False
            except Exception as e:
                logger.error(f"Failed to verify doctor: {e}")
                await db.rollback()
                return False

    async def get_user_by_login(self, login_id: str):
        """Find user by login ID (Async)."""
        async with AsyncSessionLocal() as db:
            try:
                stmt = select(UserAccount).filter(
                    (UserAccount.username == login_id)
                    | (UserAccount.email == login_id)
                    | (UserAccount.phone == login_id)
                )
                res = await db.execute(stmt)
                return res.scalars().first()
            except Exception as e:
                logger.error(f"User lookup failed: {e}")
                return None

    async def get_user_by_clerk_id(self, clerk_id: str):
        """Find user by Clerk ID (Async)."""
        async with AsyncSessionLocal() as db:
            try:
                stmt = select(UserAccount).filter(UserAccount.clerk_id == clerk_id)
                res = await db.execute(stmt)
                return res.scalars().first()
            except Exception as e:
                logger.error(f"User lookup by Clerk ID failed: {e}")
                return None

    async def log_user_activity(
        self, user_id: str, session_id: str, status: str, ip: str = None
    ):
        """Record activity (Async)."""
        async with AsyncSessionLocal() as db:
            try:
                activity = UserActivity(
                    user_id=user_id, session_id=session_id, status=status, ip_address=ip
                )
                db.add(activity)
                if status == "success":
                    stmt = select(UserAccount).filter(UserAccount.id == user_id)
                    res = await db.execute(stmt)
                    user = res.scalars().first()
                    if user:
                        user.last_login = datetime.datetime.utcnow()
                await db.commit()
            except Exception as e:
                logger.error(f"Activity logging failed: {e}")
                await db.rollback()

    async def get_or_create_case(self, user_id: str, title: str = "New Case"):
        """Manage cases (Async)."""
        if user_id == "guest":
            return None
        async with AsyncSessionLocal() as db:
            try:
                stmt = (
                    select(MedicalCase)
                    .filter(
                        MedicalCase.user_id == user_id, MedicalCase.status == "open"
                    )
                    .order_by(MedicalCase.updated_at.desc())
                )
                res = await db.execute(stmt)
                active_case = res.scalars().first()
                if active_case:
                    return active_case.id
                case_id = str(uuid.uuid4())
                new_case = MedicalCase(id=case_id, user_id=user_id, title=title)
                db.add(new_case)
                await db.commit()
                return case_id
            except Exception as e:
                logger.error(f"Case management failed: {e}")
                await db.rollback()
                return None

    # --- ADVANCED MEMORY & CASE TRACKING ---

    async def add_memory_node(self, user_id, node_type, content, meta=None):
        async with AsyncSessionLocal() as db:
            return await self._add_memory_node_db(db, user_id, node_type, content, meta)

    async def _add_memory_node_db(
        self, db: AsyncSession, user_id, node_type, content, meta=None
    ):
        try:
            enc_content = self.governance.encrypt(content)
            node = MemoryNode(
                user_id=user_id,
                node_type=node_type,
                content_encrypted=enc_content,
                metadata_json=meta or {},
            )
            db.add(node)
            await db.commit()
            return node
        except Exception as e:
            logger.error(f"Failed to add memory node: {e}")
            await db.rollback()
            return None

    async def add_memory_edge(self, user_id, source_id, target_id, relation):
        async with AsyncSessionLocal() as db:
            return await self._add_memory_edge_db(
                db, user_id, source_id, target_id, relation
            )

    async def _add_memory_edge_db(
        self, db: AsyncSession, user_id, source_id, target_id, relation
    ):
        try:
            edge = MemoryEdge(
                user_id=user_id,
                source_node_id=source_id,
                target_node_id=target_id,
                relation_type=relation,
            )
            db.add(edge)
            await db.commit()
        except Exception as e:
            logger.error(f"Failed to add memory edge: {e}")
            await db.rollback()

    async def get_memory_graph_context(self, user_id: str):
        if user_id == "guest":
            return ""
        async with AsyncSessionLocal() as db:
            try:
                stmt = (
                    select(MemoryNode)
                    .filter(MemoryNode.user_id == user_id)
                    .order_by(MemoryNode.created_at.desc())
                    .limit(15)
                )
                res = await db.execute(stmt)
                nodes = res.scalars().all()
                graph_text = "\
[USER MEMORY GRAPH - RELEVANT NODES]:\
"
                for node in nodes:
                    content = self.governance.decrypt(node.content_encrypted)
                    graph_text += f"- ({node.node_type}): {content[:200]}...\
"
                return graph_text
            except Exception as e:
                logger.error(f"Graph retrieval failed: {e}")
                return ""

    # --- Analytics & Feedback ---

    async def log_symptom(
        self, patient_id: str, symptom: str, severity: int, notes: str = None
    ):
        async with AsyncSessionLocal() as db:
            try:
                log = SymptomLog(
                    patient_id=patient_id,
                    symptom_name_encrypted=self.governance.encrypt(symptom),
                    severity=severity,
                    notes_encrypted=self.governance.encrypt(notes) if notes else None,
                )
                db.add(log)
                await db.commit()
                self.audit.log_change(
                    patient_id,
                    "PATIENT",
                    "LOG_SYMPTOM",
                    f"Symptom#{symptom}",
                    details={"severity": severity},
                )
                return True
            except Exception as e:
                logger.error(f"Symptom logging failed: {e}")
                await db.rollback()
                return False

    async def get_symptoms(self, patient_id: str, limit: int = 50):
        async with AsyncSessionLocal() as db:
            try:
                stmt = (
                    select(SymptomLog)
                    .filter(SymptomLog.patient_id == patient_id)
                    .order_by(SymptomLog.timestamp.desc())
                    .limit(limit)
                )
                res = await db.execute(stmt)
                logs = res.scalars().all()
                results = []
                for l in logs:
                    results.append(
                        {
                            "timestamp": l.timestamp.isoformat(),
                            "symptom": self.governance.decrypt(
                                l.symptom_name_encrypted
                            ),
                            "severity": l.severity,
                            "notes": (
                                self.governance.decrypt(l.notes_encrypted)
                                if l.notes_encrypted
                                else ""
                            ),
                        }
                    )
                return results
            except Exception as e:
                logger.error(f"Failed to get symptoms: {e}")
                return []

    async def save_feedback(
        self,
        user_id: str,
        role: str,
        rating: int,
        ai_response: str,
        comment: str = None,
        corrected_response: str = None,
        case_id: str = None,
    ):
        async with AsyncSessionLocal() as db:
            try:
                enc_response = self.governance.encrypt(ai_response)
                enc_comment = self.governance.encrypt(comment) if comment else None
                enc_correction = (
                    self.governance.encrypt(corrected_response)
                    if corrected_response
                    else None
                )
                new_fb = Feedback(
                    user_id=user_id,
                    role=role,
                    case_id=case_id,
                    ai_response_encrypted=enc_response,
                    rating=rating,
                    comment_encrypted=enc_comment,
                    corrected_response_encrypted=enc_correction,
                )
                db.add(new_fb)
                await db.commit()
                return new_fb.id
            except Exception as e:
                logger.error(f"Failed to save feedback: {e}")
                await db.rollback()
                return None

    async def get_feedback_by_case(self, case_id: str):
        async with AsyncSessionLocal() as db:
            try:
                stmt = (
                    select(Feedback)
                    .filter(Feedback.case_id == case_id)
                    .order_by(Feedback.timestamp.desc())
                )
                res = await db.execute(stmt)
                items = res.scalars().all()
                results = []
                for fb in items:
                    results.append(
                        {
                            "id": fb.id,
                            "user_id": fb.user_id,
                            "role": fb.role,
                            "rating": fb.rating,
                            "comment": (
                                self.governance.decrypt(fb.comment_encrypted)
                                if fb.comment_encrypted
                                else None
                            ),
                            "correction": (
                                self.governance.decrypt(fb.corrected_response_encrypted)
                                if fb.corrected_response_encrypted
                                else None
                            ),
                            "timestamp": fb.timestamp,
                        }
                    )
                return results
            except Exception as e:
                logger.error(f"Feedback retrieval failed: {e}")
                return []

    async def get_feedback_analytics(self):
        async with AsyncSessionLocal() as db:
            try:
                stmt_avg = select(func.avg(Feedback.rating))
                res_avg = await db.execute(stmt_avg)
                avg_rating = res_avg.scalar() or 0.0
                stmt_role = select(Feedback.role, func.count(Feedback.id)).group_by(
                    Feedback.role
                )
                res_role = await db.execute(stmt_role)
                role_counts = {r: c for r, c in res_role.all()}
                stmt_role_avg = select(
                    Feedback.role, func.avg(Feedback.rating)
                ).group_by(Feedback.role)
                res_role_avg = await db.execute(stmt_role_avg)
                role_avgs = {r: float(a) for r, a in res_role_avg.all()}
                return {
                    "average_rating": float(avg_rating),
                    "total_entries": sum(role_counts.values()),
                    "role_distribution": role_counts,
                    "role_averages": role_avgs,
                }
            except Exception as e:
                logger.error(f"Feedback analytics failed: {e}")
                return {}

    # --- Medication & Reminder CRUD ---

    async def log_medication(
        self, patient_id: str, name: str, dosage: str, frequency: str
    ):
        """Log a medication to the MedicationRecord analytics table (Async)."""
        async with AsyncSessionLocal() as db:
            try:
                record = MedicationRecord(
                    patient_id=patient_id,
                    medication_name_encrypted=self.governance.encrypt(name),
                    dosage_encrypted=self.governance.encrypt(dosage),
                    frequency=frequency,
                    is_active=True,
                )
                db.add(record)
                await db.commit()
                self.audit.log_change(
                    patient_id,
                    "PATIENT",
                    "LOG_MEDICATION",
                    f"Medication#{name}",
                    details={"dosage": dosage, "frequency": frequency},
                )
                return True
            except Exception as e:
                logger.error(f"Medication logging failed: {e}")
                await db.rollback()
                return False

    async def get_medications(self, patient_id: str):
        """Retrieve active medications for a patient (Async)."""
        async with AsyncSessionLocal() as db:
            try:
                stmt = (
                    select(MedicationRecord)
                    .filter(
                        MedicationRecord.patient_id == patient_id,
                        MedicationRecord.is_active == True,
                    )
                    .order_by(MedicationRecord.start_date.desc())
                )
                res = await db.execute(stmt)
                records = res.scalars().all()
                results = []
                for r in records:
                    results.append(
                        {
                            "id": r.id,
                            "name": self.governance.decrypt(
                                r.medication_name_encrypted
                            ),
                            "dosage": self.governance.decrypt(r.dosage_encrypted),
                            "frequency": r.frequency,
                            "start_date": (
                                r.start_date.isoformat() if r.start_date else ""
                            ),
                            "is_active": r.is_active,
                        }
                    )
                return results
            except Exception as e:
                logger.error(f"Failed to get medications: {e}")
                return []

    async def add_medication(
        self, user_id: str, name: str, dosage: str, frequency: str
    ):
        """Add a medication to the Medication table and create a default reminder (Async)."""
        from database.models import Medication, Reminder

        async with AsyncSessionLocal() as db:
            try:
                med = Medication(
                    user_id=user_id,
                    name_encrypted=self.governance.encrypt(name),
                    dosage_encrypted=self.governance.encrypt(dosage),
                    frequency_encrypted=self.governance.encrypt(frequency),
                    is_active=True,
                )
                db.add(med)
                await db.flush()

                self.audit.log_change(
                    user_id,
                    "PATIENT",
                    "ADD_MEDICATION",
                    f"Medication#{name}",
                    details={"dosage": dosage, "frequency": frequency},
                )

                await db.commit()
                return med.id
            except Exception as e:
                logger.error(f"Failed to add medication: {e}")
                await db.rollback()
                return None

    async def get_medications_list(self, user_id: str):
        """Retrieve medications from the Medication table (Async)."""
        from database.models import Medication

        async with AsyncSessionLocal() as db:
            try:
                stmt = (
                    select(Medication)
                    .filter(Medication.user_id == user_id, Medication.is_active == True)
                    .order_by(Medication.start_date.desc())
                )
                res = await db.execute(stmt)
                meds = res.scalars().all()
                results = []
                for m in meds:
                    results.append(
                        {
                            "id": m.id,
                            "name": self.governance.decrypt(m.name_encrypted),
                            "dosage": self.governance.decrypt(m.dosage_encrypted),
                            "frequency": self.governance.decrypt(m.frequency_encrypted),
                            "start_date": (
                                m.start_date.isoformat() if m.start_date else ""
                            ),
                            "is_active": m.is_active,
                        }
                    )
                return results
            except Exception as e:
                logger.error(f"Failed to get medications list: {e}")
                return []

    async def deactivate_medication(self, user_id: str, med_id: int):
        """Deactivate a medication (Async)."""
        from database.models import Medication

        async with AsyncSessionLocal() as db:
            try:
                stmt = select(Medication).filter(
                    Medication.id == med_id, Medication.user_id == user_id
                )
                res = await db.execute(stmt)
                med = res.scalars().first()
                if med:
                    med.is_active = False
                    med.end_date = datetime.datetime.utcnow()
                    await db.commit()
                    self.audit.log_change(
                        user_id,
                        "PATIENT",
                        "DEACTIVATE_MEDICATION",
                        f"Medication#{med_id}",
                    )
                    return True
                return False
            except Exception as e:
                logger.error(f"Failed to deactivate medication: {e}")
                await db.rollback()
                return False

    async def add_reminder(
        self, user_id: str, title: str, time_str: str, med_id: int = None
    ):
        """Add a health reminder (Async)."""
        from database.models import Reminder

        async with AsyncSessionLocal() as db:
            try:
                reminder = Reminder(
                    user_id=user_id,
                    medication_id=med_id,
                    title_encrypted=self.governance.encrypt(title),
                    reminder_time=time_str,
                    is_enabled=True,
                )
                db.add(reminder)
                await db.commit()
                self.audit.log_change(
                    user_id,
                    "PATIENT",
                    "ADD_REMINDER",
                    f"Reminder#{title}",
                    details={"time": time_str},
                )
                return reminder.id
            except Exception as e:
                logger.error(f"Failed to add reminder: {e}")
                await db.rollback()
                return None

    async def get_reminders(self, user_id: str):
        """Retrieve active reminders for a user (Async)."""
        from database.models import Reminder

        async with AsyncSessionLocal() as db:
            try:
                stmt = (
                    select(Reminder)
                    .filter(Reminder.user_id == user_id, Reminder.is_enabled == True)
                    .order_by(Reminder.id.desc())
                )
                res = await db.execute(stmt)
                rems = res.scalars().all()
                results = []
                for r in rems:
                    results.append(
                        {
                            "id": r.id,
                            "title": self.governance.decrypt(r.title_encrypted),
                            "time": r.reminder_time,
                            "is_enabled": r.is_enabled,
                            "medication_id": r.medication_id,
                            "last_triggered": (
                                r.last_triggered.isoformat()
                                if r.last_triggered
                                else None
                            ),
                        }
                    )
                return results
            except Exception as e:
                logger.error(f"Failed to get reminders: {e}")
                return []

    def get_all_active_reminders(self):
        """Retrieve all active reminders system-wide (Sync — for scheduler thread)."""
        from database.models import Reminder

        db = SessionLocal()
        try:
            rems = db.query(Reminder).filter(Reminder.is_enabled == True).all()
            results = []
            for r in rems:
                # Get user email for notification
                user = db.query(UserAccount).filter(UserAccount.id == r.user_id).first()
                email = user.email if user else "unknown@system"
                results.append(
                    {
                        "id": r.id,
                        "user_id": r.user_id,
                        "title": self.governance.decrypt(r.title_encrypted),
                        "time": r.reminder_time,
                        "email": email,
                        "last_triggered": r.last_triggered,
                    }
                )
            return results
        except Exception as e:
            logger.error(f"Failed to get all active reminders: {e}")
            return []
        finally:
            db.close()

    def mark_reminder_triggered(self, reminder_id: int):
        """Mark that a reminder was triggered (Sync — for scheduler thread)."""
        from database.models import Reminder

        db = SessionLocal()
        try:
            rem = db.query(Reminder).filter(Reminder.id == reminder_id).first()
            if rem:
                rem.last_triggered = datetime.datetime.utcnow()
                db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to mark reminder triggered: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    async def get_reports_by_patient(self, patient_id: str):
        """Retrieve medical reports by patient ID (Async)."""
        async with AsyncSessionLocal() as db:
            try:
                stmt = (
                    select(MedicalReport)
                    .filter(MedicalReport.patient_id == patient_id)
                    .order_by(MedicalReport.generated_at.desc())
                )
                res = await db.execute(stmt)
                reports = res.scalars().all()
                results = []
                for r in reports:
                    content = ""
                    try:
                        content = self.governance.decrypt(r.report_content_encrypted)
                    except Exception:
                        content = "encrypted"
                    results.append(
                        {
                            "id": r.id,
                            "generated_at": (
                                r.generated_at.isoformat() if r.generated_at else ""
                            ),
                            "report_type": r.report_type,
                            "content": content,
                            "version": r.version,
                        }
                    )
                return results
            except Exception as e:
                logger.error(f"Failed to get reports: {e}")
                return []

    async def delete_account(self, user_id: str):
        """Soft-delete a user account by marking it inactive (Async)."""
        async with AsyncSessionLocal() as db:
            try:
                stmt = select(UserAccount).filter(UserAccount.id == user_id)
                res = await db.execute(stmt)
                user = res.scalars().first()
                if user:
                    user.account_status = "deleted"
                    user.email = f"deleted_{user_id[:8]}@anon"
                    user.phone = f"000-{user_id[:8]}"
                    user.full_name_encrypted = self.governance.encrypt("Deleted User")
                    await db.commit()
                    self.audit.log_change(
                        user_id, "SYSTEM", "DELETE_ACCOUNT", f"User#{user_id}"
                    )
                    return True
                return False
            except Exception as e:
                logger.error(f"Failed to delete account: {e}")
                await db.rollback()
                return False

    def close(self):
        self.governance.close()
