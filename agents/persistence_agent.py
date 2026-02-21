"""
Persistence Agent - Manages Data Storage and Retrieval.
Handles generic, secure storage of user history and system logs.
Updated to use Governance Agent for Encryption.
"""
import uuid
import datetime
import os
import logging
from sqlalchemy.orm import Session
from database.models import SessionLocal, UserSession, Interaction, SystemLog, PatientProfile, MedicalReport, UserAction, MedicalImage, UserAccount, UserActivity, MedicalCase, MemoryNode, MemoryEdge
from agents.governance_agent import GovernanceAgent

logger = logging.getLogger(__name__)

class PersistenceAgent:
    """
    Agent responsible for saving interactions and logs to the database.
    Now integrates with Governance for Encryption.
    """
    def __init__(self):
        self.db: Session = SessionLocal()
        self.governance = GovernanceAgent()

    def create_session(self, user_id: str = "guest", mode: str = "patient") -> str:
        """Start a new tracking session."""
        session_id = str(uuid.uuid4())
        try:
            new_session = UserSession(
                id=session_id,
                user_id=user_id,
                status="active",
                interaction_mode=mode
            )
            self.db.add(new_session)
            self.db.commit()
            return session_id
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            self.db.rollback()
            return session_id 

    def save_interaction(self, session_id: str, user_input: str, result: dict, case_id: str = None):
        """Save a complete interaction flow with ENCRYPTION and Case linking."""
        try:
            # Encrypt sensitive fields
            enc_input = self.governance.encrypt(user_input)
            enc_diagnosis = self.governance.encrypt(result.get("preliminary_diagnosis", ""))
            enc_response = self.governance.encrypt(result.get("final_response", ""))
            
            interaction = Interaction(
                session_id=session_id,
                case_id=case_id,
                user_input_encrypted=enc_input,
                diagnosis_output_encrypted=enc_diagnosis,
                final_response_encrypted=enc_response,
                metadata_json=result.get("patient_info", {}),
                safety_flags={"critical_alert": result.get("critical_alert", False)}
            )
            self.db.add(interaction)
            
            # Update case risk score if applicable
            if case_id:
                case = self.db.query(MedicalCase).filter(MedicalCase.id == case_id).first()
                if case:
                    # Update risk based on critical alert
                    if result.get("critical_alert"):
                        case.risk_score = 100
                    case.updated_at = datetime.datetime.utcnow()
            
            self.db.commit()
            
            # Update Memory Graph
            self._update_memory_graph(session_id, user_input, result, case_id)
            
        except Exception as e:
            logger.error(f"Failed to save interaction: {e}")
            self.db.rollback()

    def _update_memory_graph(self, session_id, user_input, result, case_id):
        """Internal helper to populate memory nodes and edges from an interaction."""
        user_id = self.db.query(UserSession).filter(UserSession.id == session_id).first().user_id
        if user_id == "guest": return

        # 1. Create/Find Symptom Node
        symptom_summary = result.get("patient_info", {}).get("summary", "New Symptoms")
        s_node = self.add_memory_node(user_id, "Symptom", symptom_summary, {"session_id": session_id})
        
        # 2. Link to Case Node
        if case_id:
            c_node = self.db.query(MemoryNode).filter(MemoryNode.user_id == user_id, MemoryNode.node_type == "Case", MemoryNode.metadata_json["case_id"] == case_id).first()
            if not c_node:
                c_node = self.add_memory_node(user_id, "Case", f"Case: {case_id}", {"case_id": case_id})
            
            self.add_memory_edge(user_id, s_node.id, c_node.id, "relates_to")
            
        # 3. Create Diagnosis Node if reasoning exists
        diag = result.get("preliminary_diagnosis")
        if diag:
            d_node = self.add_memory_node(user_id, "Diagnosis", diag, {"session_id": session_id})
            self.add_memory_edge(user_id, s_node.id, d_node.id, "diagnosed_as")

    def log_system_event(self, level: str, component: str, message: str, details: dict = None, session_id: str = None):
        """Log a system event or error."""
        try:
            log_entry = SystemLog(
                level=level,
                component=component,
                message=message,
                details=details or {},
                session_id=session_id
            )
            self.db.add(log_entry)
            self.db.commit()
        except Exception as e:
            logger.error(f"DB Logging failed: {e}")

    def get_user_history(self, user_id: str, limit: int = 10):
        """Retrieve past sessions for a user, DECRYPTING data."""
        try:
            # This just gets sessions. To get interactions, we need to query interactions.
            sessions = self.db.query(UserSession).filter(
                UserSession.user_id == user_id
            ).order_by(UserSession.start_time.desc()).limit(limit).all()
            return sessions
        except Exception as e:
            logger.error(f"Failed to retrieve history: {e}")
            return []

    def get_long_term_memory(self, user_id: str, limit_sessions: int = 3):
        """Fetch and format past interactions for LLM context."""
        try:
            sessions = self.db.query(UserSession).filter(UserSession.user_id == user_id).order_by(UserSession.start_time.desc()).limit(limit_sessions).all()
            memory_text = ""
            for s in sessions:
                interactions = self.db.query(Interaction).filter(Interaction.session_id == s.id).all()
                if not interactions: continue
                memory_text += f"\n--- PAST SESSION: {s.id} ({s.start_time.strftime('%Y-%m-%d')}) ---\n"
                for i in interactions:
                    u_in = self.governance.decrypt(i.user_input_encrypted)
                    diag = self.governance.decrypt(i.diagnosis_output_encrypted)
                    memory_text += f"User: {u_in}\nAI Diagnosis: {diag}\n"
            return memory_text if memory_text else "No previous medical history found."
        except Exception as e:
            logger.error(f"Failed to fetch long term memory: {e}")
            return "Error loading history."

    
    # -----------------------------------------------------
    # Patient Profile & Reporting Methods
    # -----------------------------------------------------
    
    def get_patient_profile(self, user_id: str):
        """Retrieve decrypted patient profile."""
        try:
            profile = self.db.query(PatientProfile).filter(PatientProfile.id == user_id).first()
            if not profile:
                return None
            
            # Decrypt fields
            decrypted_name = self.governance.decrypt(profile.name_encrypted) if profile.name_encrypted else ""
            decrypted_history = self.governance.decrypt(profile.medical_history_encrypted) if profile.medical_history_encrypted else ""
            
            return {
                "id": profile.id,
                "name": decrypted_name,
                "age": profile.age,
                "gender": profile.gender,
                "medical_history": decrypted_history, # Expect JSON
                "created_at": profile.created_at
            }
        except Exception as e:
            logger.error(f"Failed to fetch patient profile: {e}")
            return None

    def upsert_patient_profile(self, user_id: str, name: str, age: int, gender: str, history_json: str):
        """Create or Update patient profile securely."""
        try:
            profile = self.db.query(PatientProfile).filter(PatientProfile.id == user_id).first()
            enc_name = self.governance.encrypt(name)
            enc_history = self.governance.encrypt(history_json)
            
            if not profile:
                profile = PatientProfile(
                    id=user_id,
                    name_encrypted=enc_name,
                    age=age,
                    gender=gender,
                    medical_history_encrypted=enc_history
                )
                self.db.add(profile)
            else:
                profile.name_encrypted = enc_name
                profile.age = age
                profile.gender = gender
                profile.medical_history_encrypted = enc_history
            
            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to upsert profile: {e}")
            self.db.rollback()
            return False

    def save_medical_report(self, session_id: str, patient_id: str, content_json: str, report_type: str = "comprehensive", lang: str = "en", status: str = "pending"):
        """Save a new version of a generated medical report."""
        try:
            # Check if profile exists; if not, create a placeholder? Best logic: ensure profile created by PatientAgent first.
            # Assuming profile exists or we handle FK error.
            if not self.db.query(PatientProfile).filter(PatientProfile.id == patient_id).first():
                # Auto-create minimal profile if missing (Guest)
                self.upsert_patient_profile(patient_id, "Guest Patient", 0, "Unknown", "{}")
            
            # Encrypt report content
            enc_content = self.governance.encrypt(content_json)
            
            # Get latest version
            last_report = self.db.query(MedicalReport).filter(
                MedicalReport.patient_id == patient_id
            ).order_by(MedicalReport.version.desc()).first()
            
            new_version = (last_report.version + 1) if last_report else 1
            
            new_report = MedicalReport(
                patient_id=patient_id,
                session_id=session_id,
                report_content_encrypted=enc_content,
                report_type=report_type,
                language=lang,
                version=new_version,
                status=status # pending review or approved
            )
            self.db.add(new_report)
            self.db.commit()
            return new_report.id
        except Exception as e:
            logger.error(f"Failed to save medical report: {e}")
            self.db.rollback()
            return None

    def get_reports_by_patient(self, user_id: str):
        """Retrieve all medical reports for a patient, decrypted."""
        try:
            reports = self.db.query(MedicalReport).filter(MedicalReport.patient_id == user_id).order_by(MedicalReport.generated_at.desc()).all()
            results = []
            for r in reports:
                results.append({
                    "id": r.id,
                    "generated_at": r.generated_at,
                    "report_type": r.report_type,
                    "language": r.language,
                    "version": r.version,
                    "status": r.status,
                    "content": json.loads(self.governance.decrypt(r.report_content_encrypted))
                })
            return results
        except Exception as e:
            logger.error(f"Failed to fetch reports: {e}")
            return []

    def save_medical_image(self, session_id: str, image_path: str, findings: dict, patient_id: str = None):
        """Save medical image metadata and analysis securely."""
        try:
            # Encrypt sensitive fields
            enc_path = self.governance.encrypt(image_path)
            enc_findings = self.governance.encrypt(str(findings.get("visual_findings", "")))
            
            new_image = MedicalImage(
                session_id=session_id,
                patient_id=patient_id,
                image_path_encrypted=enc_path,
                original_filename=os.path.basename(image_path),
                visual_findings_encrypted=enc_findings,
                possible_conditions_json=findings.get("possible_conditions", []),
                confidence_score=int(findings.get("confidence", 0) * 100),
                severity_level=findings.get("severity_level", "low"),
                requires_human_review=findings.get("requires_human_review", False)
            )
            self.db.add(new_image)
            self.db.commit()
            return new_image.id
        except Exception as e:
            logger.error(f"Failed to save medical image: {e}")
            self.db.rollback()
            return None

    def get_session_images(self, session_id: str):
        """Retrieve all images for a session, decrypted."""
        try:
            images = self.db.query(MedicalImage).filter(MedicalImage.session_id == session_id).all()
            result = []
            for img in images:
                result.append({
                    "id": img.id,
                    "timestamp": img.timestamp,
                    "image_path": self.governance.decrypt(img.image_path_encrypted),
                    "visual_findings": self.governance.decrypt(img.visual_findings_encrypted),
                    "confidence": img.confidence_score / 100.0,
                    "severity": img.severity_level
                })
            return result
        except Exception as e:
            logger.error(f"Failed to fetch session images: {e}")
            return []

    def save_user_action(self, session_id: str, action_type: str, element_id: str, details: dict = None, audit_tag: str = "UX"):
        """Save a granular user UI action."""
        try:
            action = UserAction(
                session_id=session_id,
                action_type=action_type,
                element_id=element_id,
                details=details or {},
                audit_tag=audit_tag
            )
            self.db.add(action)
            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to save user action: {e}")
            self.db.rollback()
            return False

    def close(self):
        self.db.close()
        self.governance.close()

    # --- IDENTITY & AUTHENTICATION ---
    def register_user(self, username: str, email: str, phone: str, password: str, full_name: str, 
                      role: str = "patient", gender: str = None, age: int = None, 
                      country: str = None, meta: dict = None):
        """Create a new user account securely with role and demographic data."""
        try:
            user_id = str(uuid.uuid4())
            hashed_pwd = self.governance.hash_password(password)
            enc_name = self.governance.encrypt(full_name)
            enc_meta = self.governance.encrypt(str(meta or {}))
            
            user = UserAccount(
                id=user_id,
                username=username,
                email=email,
                phone=phone,
                full_name_encrypted=enc_name,
                password_hash=hashed_pwd,
                role=role,
                gender=gender,
                age=age,
                country=country,
                interaction_mode=role if role in ["patient", "doctor"] else "patient",
                profile_metadata_encrypted=enc_meta
            )
            self.db.add(user)
            self.db.commit()
            
            # Auto-create patient profile
            self.upsert_patient_profile(user_id, full_name, age or 0, gender or "Unknown", "{}")
            
            return user_id
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            self.db.rollback()
            return None

    def update_interaction_mode(self, user_id: str, mode: str):
        """Update user's default interaction mode."""
        try:
            user = self.db.query(UserAccount).filter(UserAccount.id == user_id).first()
            if user:
                user.interaction_mode = mode
                self.db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to update interaction mode: {e}")
            self.db.rollback()
            return False

    def verify_doctor(self, user_id: str, license_number: str, specialization: str):
        """Verify doctor credentials and update account."""
        try:
            user = self.db.query(UserAccount).filter(UserAccount.id == user_id).first()
            if user and user.role == "doctor":
                user.license_number = license_number
                user.specialization = specialization
                user.doctor_verified = True
                self.db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to verify doctor: {e}")
            self.db.rollback()
            return False

    def get_user_by_login(self, login_id: str):
        """Find user by username, email, or phone."""
        return self.db.query(UserAccount).filter(
            (UserAccount.username == login_id) | 
            (UserAccount.email == login_id) | 
            (UserAccount.phone == login_id)
        ).first()

    def log_user_activity(self, user_id: str, session_id: str, status: str, ip: str = None):
        """Record login/logout activity."""
        try:
            activity = UserActivity(
                user_id=user_id,
                session_id=session_id,
                status=status,
                ip_address=ip
            )
            self.db.add(activity)
            if status == "success":
                user = self.db.query(UserAccount).filter(UserAccount.id == user_id).first()
                if user:
                    user.last_login = datetime.datetime.utcnow()
            self.db.commit()
        except Exception as e:
            logger.error(f"Activity logging failed: {e}")
            self.db.rollback()

    # --- ADVANCED MEMORY & CASE TRACKING ---
    def get_or_create_case(self, user_id: str, title: str = "New Case"):
        """Manage persistent medical cases."""
        if user_id == "guest": return None
        try:
            # Find open case
            active_case = self.db.query(MedicalCase).filter(
                MedicalCase.user_id == user_id,
                MedicalCase.status == "open"
            ).order_by(MedicalCase.updated_at.desc()).first()
            
            if active_case:
                return active_case.id
            
            # Create new
            case_id = str(uuid.uuid4())
            new_case = MedicalCase(id=case_id, user_id=user_id, title=title)
            self.db.add(new_case)
            self.db.commit()
            return case_id
        except Exception as e:
            logger.error(f"Case management failed: {e}")
            return None

    def add_memory_node(self, user_id, node_type, content, meta=None):
        try:
            enc_content = self.governance.encrypt(content)
            node = MemoryNode(user_id=user_id, node_type=node_type, content_encrypted=enc_content, metadata_json=meta or {})
            self.db.add(node)
            self.db.commit()
            return node
        except Exception as e:
            logger.error(f"Failed to add memory node: {e}")
            self.db.rollback()
            return None

    def add_memory_edge(self, user_id, source_id, target_id, relation):
        try:
            edge = MemoryEdge(user_id=user_id, source_node_id=source_id, target_node_id=target_id, relation_type=relation)
            self.db.add(edge)
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to add memory edge: {e}")
            self.db.rollback()

    def get_memory_graph_context(self, user_id: str):
        """Retrieve and format the memory graph as contextual text."""
        if user_id == "guest": return ""
        try:
            # For brevity, we'll get the last 10 nodes and their relationships
            nodes = self.db.query(MemoryNode).filter(MemoryNode.user_id == user_id).order_by(MemoryNode.created_at.desc()).limit(15).all()
            graph_text = "\n[USER MEMORY GRAPH - RELEVANT NODES]:\n"
            for node in nodes:
                content = self.governance.decrypt(node.content_encrypted)
                graph_text += f"- ({node.node_type}): {content[:200]}...\n"
            return graph_text
        except Exception as e:
            logger.error(f"Graph retrieval failed: {e}")
            return ""

    # --- MEDICATION & REMINDER PERSISTENCE ---
    def add_medication(self, user_id: str, name: str, dosage: str, frequency: str):
        try:
            from database.models import Medication
            med = Medication(
                user_id=user_id,
                name_encrypted=self.governance.encrypt(name),
                dosage_encrypted=self.governance.encrypt(dosage),
                frequency_encrypted=self.governance.encrypt(frequency)
            )
            self.db.add(med)
            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to add medication: {e}")
            self.db.rollback()
            return False

    def get_medications(self, user_id: str):
        try:
            from database.models import Medication
            meds = self.db.query(Medication).filter(Medication.user_id == user_id, Medication.is_active == True).all()
            results = []
            for m in meds:
                results.append({
                    "id": m.id,
                    "name": self.governance.decrypt(m.name_encrypted),
                    "dosage": self.governance.decrypt(m.dosage_encrypted),
                    "frequency": self.governance.decrypt(m.frequency_encrypted)
                })
            return results
        except Exception as e:
            logger.error(f"Failed to get medications: {e}")
            return []

    def add_reminder(self, user_id: str, title: str, time_str: str, med_id: int = None):
        try:
            from database.models import Reminder
            rem = Reminder(
                user_id=user_id,
                medication_id=med_id,
                title_encrypted=self.governance.encrypt(title),
                reminder_time=time_str
            )
            self.db.add(rem)
            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to add reminder: {e}")
            self.db.rollback()
            return False

    # --- ACCOUNT MANAGEMENT ---
    def delete_account(self, user_id: str):
        """Perform a safe account depletion (Soft delete for audit compliance)."""
        try:
            user = self.db.query(UserAccount).filter(UserAccount.id == user_id).first()
            if user:
                user.account_status = "deleted"
                # Anonymize sensitive fields
                user.username = f"deleted_{user_id[:8]}"
                user.email = f"deleted_{user_id[:8]}@medagent.org"
                user.phone = f"deleted_{user_id[:8]}"
                self.db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Account deletion failed: {e}")
            self.db.rollback()
            return False

    def close(self):
        self.db.close()
