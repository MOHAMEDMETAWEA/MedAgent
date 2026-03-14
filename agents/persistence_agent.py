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
from database.models import SessionLocal, get_db, UserSession, Interaction, SystemLog, PatientProfile, MedicalReport, UserAction, MedicalImage, UserAccount, UserActivity, MedicalCase, MemoryNode, MemoryEdge, UserRole, SymptomLog, MedicationRecord
from agents.governance_agent import GovernanceAgent
from agents.audit_agent import AuditAgent
from config import settings
import hashlib
import json

logger = logging.getLogger(__name__)

class PersistenceAgent:
    """
    Agent responsible for saving interactions and logs to the database.
    Now integrates with Governance for Encryption.
    """
    def __init__(self):
        self.governance = GovernanceAgent()
        self.audit = AuditAgent()

    def _get_db(self):
        """Create a fresh DB session for each operation."""
        return SessionLocal()

    def create_session(self, user_id: str = "guest", mode: str = "patient") -> str:
        """Start a new tracking session."""
        session_id = str(uuid.uuid4())
        db = self._get_db()
        try:
            new_session = UserSession(
                id=session_id,
                user_id=user_id,
                status="active",
                interaction_mode=mode
            )
            db.add(new_session)
            db.commit()
            return session_id
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            db.rollback()
            return session_id
        finally:
            db.close()

    def _save_interaction_db(self, db, session_id: str, user_input: str, result: dict, case_id: str = None):
        """Internal helper to save interaction using provided DB session."""
        try:
            # Encrypt sensitive fields
            enc_input = self.governance.encrypt(user_input)
            enc_diagnosis = self.governance.encrypt(result.get("preliminary_diagnosis", ""))
            enc_response = self.governance.encrypt(result.get("final_response", ""))
            
            # Derive lineage/observability fields
            prompt_version = result.get("prompt_version")
            model_used = result.get("model_used", getattr(settings, "OPENAI_MODEL", None))
            secondary_model = result.get("secondary_model")
            confidence_score = result.get("confidence_score")
            risk_level = result.get("risk_level")
            latency_ms = result.get("latency_ms", 0)
            
            # 4. Compute chainable audit hash
            # Fetch previous interaction hash in this session for chaining
            prev_interaction = db.query(Interaction).filter(Interaction.session_id == session_id).order_by(Interaction.timestamp.desc()).first()
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
                secondary_model=secondary_model,
                confidence_score=confidence_score,
                risk_level=risk_level,
                audit_hash=audit_hash,
                previous_audit_hash=prev_hash,
                latency_ms=latency_ms
            )
            db.add(interaction)
            
            # Update case risk score if applicable
            if case_id:
                case = db.query(MedicalCase).filter(MedicalCase.id == case_id).first()
                if case:
                    # Update risk based on critical alert
                    if result.get("critical_alert"):
                        case.risk_score = 100
                    case.updated_at = datetime.datetime.utcnow()
            
            db.commit()
            
            # Update Memory Graph
            self._update_memory_graph_with_db(db, session_id, user_input, result, case_id)
            
        except Exception as e:
            logger.error(f"Failed to save interaction: {e}")
            db.rollback()

    def save_interaction(self, session_id: str, user_input: str, result: dict, case_id: str = None):
        """Save a complete interaction flow with ENCRYPTION and Case linking."""
        db = self._get_db()
        return self._save_interaction_db(db, session_id, user_input, result, case_id)

    def _update_memory_graph_with_db(self, db, session_id, user_input, result, case_id):
        """Internal helper to populate memory nodes and edges from an interaction."""
        user_session = db.query(UserSession).filter(UserSession.id == session_id).first()
        if not user_session: return
        user_id = user_session.user_id
        if user_id == "guest": return

        # 1. Create/Find Symptom Node
        symptom_summary = result.get("patient_info", {}).get("summary", "New Symptoms")
        s_node = self._add_memory_node_db(db, user_id, "Symptom", symptom_summary, {"session_id": session_id})
        
        # 2. Link to Case Node
        c_node = None
        if case_id:
            c_node = db.query(MemoryNode).filter(
                MemoryNode.user_id == user_id, 
                MemoryNode.node_type == "Case"
            ).all() # Filter manually for JSON field in SQLite
            c_node = next((n for n in c_node if n.metadata_json.get("case_id") == case_id), None)
            
            if not c_node:
                c_node = self._add_memory_node_db(db, user_id, "Case", f"Case: {case_id}", {"case_id": case_id})
            
            self._add_memory_edge_db(db, user_id, s_node.id, c_node.id, "relates_to")
            
        # 3. Create Diagnosis & Reasoning Nodes
        diag = result.get("preliminary_diagnosis")
        if diag:
            d_node = self._add_memory_node_db(db, user_id, "Diagnosis", diag, {"session_id": session_id})
            self._add_memory_edge_db(db, user_id, s_node.id, d_node.id, "diagnosed_as")
            if c_node: self._add_memory_edge_db(db, user_id, d_node.id, c_node.id, "relates_to")

        # 4. Reason (Tree of Thought) node
        tot = result.get("doctor_notes")
        if tot:
            r_node = self._add_memory_node_db(db, user_id, "Reasoning", tot, {"session_id": session_id})
            if c_node: self._add_memory_edge_db(db, user_id, r_node.id, c_node.id, "explains")

        # 5. Report Node
        report_id = result.get("report_id")
        if report_id:
            rp_node = self._add_memory_node_db(db, user_id, "Report", f"Clinical Report #{report_id}", {"report_id": report_id, "session_id": session_id})
            if c_node: self._add_memory_edge_db(db, user_id, rp_node.id, c_node.id, "documented_in")

    def log_system_event(self, level: str, component: str, message: str, details: dict = None, session_id: str = None):
        """Log a system event or error."""
        db = self._get_db()
        try:
            # Optional PHI redaction of message/details
            redacted_message = message
            redacted_details = details or {}
            try:
                from agents.safety.privacy_audit import PrivacyAuditLayer
                pal = PrivacyAuditLayer()
                redacted_message = pal.redact_phi(message) if message else message
                # Best-effort redaction of details dict stringified
                if redacted_details:
                    redacted_details = {"_redacted": pal.redact_phi(str(redacted_details))}
            except Exception:
                pass
            log_entry = SystemLog(
                level=level,
                component=component,
                message=redacted_message,
                details=redacted_details,
                session_id=session_id
            )
            db.add(log_entry)
            db.commit()
        except Exception as e:
            logger.error(f"DB Logging failed: {e}")
            db.rollback()
        finally:
            db.close()

    def get_user_history(self, user_id: str, limit: int = 10):
        """Retrieve past sessions for a user, DECRYPTING data."""
        db = self._get_db()
        try:
            # This just gets sessions. To get interactions, we need to query interactions.
            sessions = db.query(UserSession).filter(
                UserSession.user_id == user_id
            ).order_by(UserSession.start_time.desc()).limit(limit).all()
            return sessions
        except Exception as e:
            logger.error(f"Failed to retrieve history: {e}")
            return []
        finally:
            db.close()

    def get_long_term_memory(self, user_id: str, limit_sessions: int = 3):
        """Fetch and format past interactions for LLM context."""
        db = self._get_db()
        try:
            sessions = db.query(UserSession).filter(UserSession.user_id == user_id).order_by(UserSession.start_time.desc()).limit(limit_sessions).all()
            memory_text = ""
            for s in sessions:
                interactions = db.query(Interaction).filter(Interaction.session_id == s.id).all()
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
        finally:
            db.close()

    
    # -----------------------------------------------------
    # Patient Profile & Reporting Methods
    # -----------------------------------------------------
    
    def get_patient_profile(self, user_id: str):
        """Retrieve decrypted patient profile."""
        db = self._get_db()
        try:
            profile = db.query(PatientProfile).filter(PatientProfile.id == user_id).first()
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
        finally:
            db.close()

    def upsert_patient_profile(self, user_id: str, name: str, age: int, gender: str, history_json: str):
        """Create or Update patient profile securely."""
        db = self._get_db()
        try:
            return self._upsert_patient_profile_db(db, user_id, name, age, gender, history_json)
        finally:
            db.close()

    def _upsert_patient_profile_db(self, db, user_id: str, name: str, age: int, gender: str, history_json: str):
        """Internal helper for patient profile upsert."""
        try:
            profile = db.query(PatientProfile).filter(PatientProfile.id == user_id).first()
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
                db.add(profile)
            else:
                profile.name_encrypted = enc_name
                profile.age = age
                profile.gender = gender
                profile.medical_history_encrypted = enc_history
            
            db.commit()
            self.audit.log_change(user_id, "SYSTEM", "UPDATE_PROFILE", f"Profile#{user_id}", details={"age": age, "gender": gender})
            return True
        except Exception as e:
            logger.error(f"Failed to upsert profile: {e}")
            db.rollback()
            return False

    def save_medical_report(self, session_id: str, patient_id: str, content_json: str, report_type: str = "comprehensive", lang: str = "en", status: str = "pending"):
        """Save a new version of a generated medical report."""
        db = self._get_db()
        try:
            # Check if profile exists; if not, create a placeholder? Best logic: ensure profile created by PatientAgent first.
            # Assuming profile exists or we handle FK error.
            if not db.query(PatientProfile).filter(PatientProfile.id == patient_id).first():
                # Auto-create minimal profile if missing (Guest)
                self._upsert_patient_profile_db(db, patient_id, "Guest Patient", 0, "Unknown", "{}")
            
            # Encrypt report content
            enc_content = self.governance.encrypt(content_json)
            
            # Get latest version
            last_report = db.query(MedicalReport).filter(
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
            db.add(new_report)
            db.commit()
            return new_report.id
        except Exception as e:
            logger.error(f"Failed to save medical report: {e}")
            db.rollback()
            return None
        finally:
            db.close()

    def get_reports_by_patient(self, user_id: str):
        """Retrieve all medical reports for a patient, decrypted."""
        db = self._get_db()
        try:
            reports = db.query(MedicalReport).filter(MedicalReport.patient_id == user_id).order_by(MedicalReport.generated_at.desc()).all()
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
        finally:
            db.close()

    def save_medical_image(self, session_id: str, image_path: str, findings: dict, patient_id: str = None, case_id: str = None):
        """Save medical image metadata and analysis securely with Case linking."""
        db = self._get_db()
        try:
            # Encrypt sensitive fields
            enc_path = self.governance.encrypt(image_path)
            enc_findings = self.governance.encrypt(str(findings.get("visual_findings", "")))
            
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
                requires_human_review=findings.get("requires_human_review", False)
            )
            db.add(new_image)
            db.commit()
            
            # Update memory graph with Image node
            if patient_id and patient_id != "guest":
                self._update_memory_graph_with_image_db(db, patient_id, session_id, new_image.id, findings, case_id)
            
            return new_image.id
        except Exception as e:
            logger.error(f"Failed to save medical image: {e}")
            db.rollback()
            return None
        finally:
            db.close()

    def _update_memory_graph_with_image_db(self, db, user_id, session_id, image_id, findings, case_id):
        """Link image to case and findings in the memory graph using provided DB session."""
        try:
            # 1. Create Image Node
            img_node = self._add_memory_node_db(db, user_id, "Image", f"Medical Image: {findings.get('image_type', 'Visual Scan')}", {"image_id": image_id, "session_id": session_id})
            
            # 2. Link to Case
            if case_id:
                case_nodes = db.query(MemoryNode).filter(MemoryNode.user_id == user_id, MemoryNode.node_type == "Case").all()
                case_node = next((n for n in case_nodes if n.metadata_json.get("case_id") == case_id), None)
                if case_node:
                    self._add_memory_edge_db(db, user_id, img_node.id, case_node.id, "based_on")
            
            # 3. Create Analysis Node
            analysis_content = findings.get("visual_findings", "Image Analysis Result")
            analysis_node = self._add_memory_node_db(db, user_id, "Analysis", analysis_content, {"image_id": image_id})
            self._add_memory_edge_db(db, user_id, img_node.id, analysis_node.id, "analyzed_as")
            
        except Exception as e:
            logger.error(f"Failed to update memory graph with image: {e}")

    def get_session_images(self, session_id: str):
        """Retrieve all images for a session, decrypted."""
        db = self._get_db()
        try:
            images = db.query(MedicalImage).filter(MedicalImage.session_id == session_id).all()
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
        finally:
            db.close()

    def save_user_action(self, session_id: str, action_type: str, element_id: str, details: dict = None, audit_tag: str = "UX"):
        """Save a granular user UI action."""
        db = self._get_db()
        try:
            action = UserAction(
                session_id=session_id,
                action_type=action_type,
                element_id=element_id,
                details=details or {},
                audit_tag=audit_tag
            )
            db.add(action)
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to save user action: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    def close(self):
        self.governance.close()

    # --- IDENTITY & AUTHENTICATION ---
    def register_user(self, username: str, email: str, phone: str, password: str, full_name: str, 
                      role: str = "patient", gender: str = None, age: int = None, 
                      country: str = None, meta: dict = None, clerk_id: str = None):
        """Create a new user account securely with role and demographic data."""
        db = self._get_db()
        try:
            user_id = str(uuid.uuid4())
            hashed_pwd = self.governance.hash_password(password)
            enc_name = self.governance.encrypt(full_name)
            enc_meta = self.governance.encrypt(str(meta or {}))
            
            # Coerce role string to UserRole enum
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
                interaction_mode=role if role in ["patient", "doctor"] else "patient",
                profile_metadata_encrypted=enc_meta,
                clerk_id=clerk_id
            )
            db.add(user)
            db.commit()
            
            self.audit.log_change(user_id, role, "REGISTER_USER", f"User#{user_id}", details={"username": username, "email": email, "clerk_id": clerk_id})
            
            # Auto-create patient profile
            self._upsert_patient_profile_db(db, user_id, full_name, age or 0, gender or "Unknown", "{}")
            
            return user_id
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            db.rollback()
            return None
        finally:
            db.close()

    def update_interaction_mode(self, user_id: str, mode: str):
        """Update user's default interaction mode."""
        db = self._get_db()
        try:
            user = db.query(UserAccount).filter(UserAccount.id == user_id).first()
            if user:
                user.interaction_mode = mode
                db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to update interaction mode: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    def verify_doctor(self, user_id: str, license_number: str, specialization: str):
        """Verify doctor credentials and update account."""
        db = self._get_db()
        try:
            user = db.query(UserAccount).filter(UserAccount.id == user_id).first()
            if user and user.role == "doctor":
                user.license_number = license_number
                user.specialization = specialization
                user.doctor_verified = True
                db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to verify doctor: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    def get_user_by_login(self, login_id: str):
        """Find user by username, email, or phone."""
        db = self._get_db()
        try:
            return db.query(UserAccount).filter(
                (UserAccount.username == login_id) | 
                (UserAccount.email == login_id) | 
                (UserAccount.phone == login_id)
            ).first()
        except Exception as e:
            logger.error(f"User lookup failed: {e}")
            return None
        finally:
            db.close()

    def get_user_by_clerk_id(self, clerk_id: str):
        """Find user by their Clerk ID."""
        db = self._get_db()
        try:
            return db.query(UserAccount).filter(UserAccount.clerk_id == clerk_id).first()
        except Exception as e:
            logger.error(f"User lookup by Clerk ID failed: {e}")
            return None
        finally:
            db.close()

    def log_user_activity(self, user_id: str, session_id: str, status: str, ip: str = None):
        """Record login/logout activity."""
        db = self._get_db()
        try:
            activity = UserActivity(
                user_id=user_id,
                session_id=session_id,
                status=status,
                ip_address=ip
            )
            db.add(activity)
            if status == "success":
                user = db.query(UserAccount).filter(UserAccount.id == user_id).first()
                if user:
                    user.last_login = datetime.datetime.utcnow()
            db.commit()
        except Exception as e:
            logger.error(f"Activity logging failed: {e}")
            db.rollback()
        finally:
            db.close()

    # --- ADVANCED MEMORY & CASE TRACKING ---
    def get_or_create_case(self, user_id: str, title: str = "New Case"):
        """Manage persistent medical cases."""
        if user_id == "guest": return None
        db = self._get_db()
        try:
            # Find open case
            active_case = db.query(MedicalCase).filter(
                MedicalCase.user_id == user_id,
                MedicalCase.status == "open"
            ).order_by(MedicalCase.updated_at.desc()).first()
            
            if active_case:
                return active_case.id
            
            # Create new
            case_id = str(uuid.uuid4())
            new_case = MedicalCase(id=case_id, user_id=user_id, title=title)
            db.add(new_case)
            db.commit()
            return case_id
        except Exception as e:
            logger.error(f"Case management failed: {e}")
            return None
        finally:
            db.close()

    def add_memory_node(self, user_id, node_type, content, meta=None):
        db = self._get_db()
        try:
            return self._add_memory_node_db(db, user_id, node_type, content, meta)
        finally:
            db.close()

    def _add_memory_node_db(self, db, user_id, node_type, content, meta=None):
        try:
            enc_content = self.governance.encrypt(content)
            node = MemoryNode(user_id=user_id, node_type=node_type, content_encrypted=enc_content, metadata_json=meta or {})
            db.add(node)
            db.commit()
            return node
        except Exception as e:
            logger.error(f"Failed to add memory node: {e}")
            db.rollback()
            return None

    def add_memory_edge(self, user_id, source_id, target_id, relation):
        db = self._get_db()
        try:
            return self._add_memory_edge_db(db, user_id, source_id, target_id, relation)
        finally:
            db.close()

    def _add_memory_edge_db(self, db, user_id, source_id, target_id, relation):
        try:
            edge = MemoryEdge(user_id=user_id, source_node_id=source_id, target_node_id=target_id, relation_type=relation)
            db.add(edge)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to add memory edge: {e}")
            db.rollback()

    def get_memory_graph_context(self, user_id: str):
        """Retrieve and format the memory graph as contextual text."""
        if user_id == "guest": return ""
        db = self._get_db()
        try:
            # For brevity, we'll get the last 10 nodes and their relationships
            nodes = db.query(MemoryNode).filter(MemoryNode.user_id == user_id).order_by(MemoryNode.created_at.desc()).limit(15).all()
            graph_text = "\n[USER MEMORY GRAPH - RELEVANT NODES]:\n"
            for node in nodes:
                content = self.governance.decrypt(node.content_encrypted)
                graph_text += f"- ({node.node_type}): {content[:200]}...\n"
            return graph_text
        except Exception as e:
            logger.error(f"Graph retrieval failed: {e}")
            return ""
        finally:
            db.close()

    # --- MEDICATION & REMINDER PERSISTENCE ---
    def add_medication(self, user_id: str, name: str, dosage: str, frequency: str):
        db = self._get_db()
        try:
            from database.models import Medication
            med = Medication(
                user_id=user_id,
                name_encrypted=self.governance.encrypt(name),
                dosage_encrypted=self.governance.encrypt(dosage),
                frequency_encrypted=self.governance.encrypt(frequency)
            )
            db.add(med)
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to add medication: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    def get_medications(self, user_id: str):
        db = self._get_db()
        try:
            from database.models import Medication
            meds = db.query(Medication).filter(Medication.user_id == user_id, Medication.is_active == True).all()
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
        finally:
            db.close()

    def add_reminder(self, user_id: str, title: str, time_str: str, med_id: int = None):
        db = self._get_db()
        try:
            from database.models import Reminder
            rem = Reminder(
                user_id=user_id,
                medication_id=med_id,
                title_encrypted=self.governance.encrypt(title),
                reminder_time=time_str
            )
            db.add(rem)
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to add reminder: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    def get_reminders(self, user_id: str):
        db = self._get_db()
        try:
            from database.models import Reminder
            rems = db.query(Reminder).filter(Reminder.user_id == user_id).all()
            results = []
            for r in rems:
                results.append({
                    "id": r.id,
                    "title": self.governance.decrypt(r.title_encrypted),
                    "time": r.reminder_time,
                    "medication_id": r.medication_id,
                    "is_enabled": r.is_enabled
                })
            return results
        finally:
            db.close()

    def get_all_active_reminders(self):
        """Used by the background scheduler to fetch all enabled reminders."""
        db = self._get_db()
        try:
            from database.models import Reminder, UserAccount
            rems = db.query(Reminder, UserAccount.email).join(
                UserAccount, Reminder.user_id == UserAccount.id
            ).filter(Reminder.is_enabled == True).all()
            
            results = []
            for r, email in rems:
                results.append({
                    "id": r.id,
                    "user_id": r.user_id,
                    "email": email,
                    "title": self.governance.decrypt(r.title_encrypted),
                    "time": r.reminder_time,
                    "last_triggered": r.last_triggered
                })
            return results
        finally:
            db.close()

    def mark_reminder_triggered(self, reminder_id: int):
        db = self._get_db()
        try:
            from database.models import Reminder
            rem = db.query(Reminder).filter(Reminder.id == reminder_id).first()
            if rem:
                rem.last_triggered = datetime.datetime.utcnow()
                db.commit()
        finally:
            db.close()

    # --- ACCOUNT MANAGEMENT ---
    def delete_account(self, user_id: str):
        """Perform a safe account depletion (Soft delete for audit compliance)."""
        db = self._get_db()
        try:
            user = db.query(UserAccount).filter(UserAccount.id == user_id).first()
            if user:
                user.account_status = "deleted"
                # Anonymize sensitive fields
                user.username = f"deleted_{user_id[:8]}"
                user.email = f"deleted_{user_id[:8]}@medagent.org"
                user.phone = f"deleted_{user_id[:8]}"
                db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Account deletion failed: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    # --- ANALYTICS: SYMPTOMS & MEDICATIONS ---
    def log_symptom(self, patient_id: str, symptom: str, severity: int, notes: str = None):
        """Record a patient symptom with severity."""
        db = self._get_db()
        try:
            log = SymptomLog(
                patient_id=patient_id,
                symptom_name_encrypted=self.governance.encrypt(symptom),
                severity=severity,
                notes_encrypted=self.governance.encrypt(notes) if notes else None
            )
            db.add(log)
            db.commit()
            self.audit.log_change(patient_id, "PATIENT", "LOG_SYMPTOM", f"Symptom#{symptom}", details={"severity": severity})
            return True
        finally:
            db.close()

    def get_symptoms(self, patient_id: str, limit: int = 50):
        """Retrieve symptom history for a patient."""
        db = self._get_db()
        try:
            logs = db.query(SymptomLog).filter(SymptomLog.patient_id == patient_id).order_by(SymptomLog.timestamp.desc()).limit(limit).all()
            results = []
            for l in logs:
                results.append({
                    "timestamp": l.timestamp.isoformat(),
                    "symptom": self.governance.decrypt(l.symptom_name_encrypted),
                    "severity": l.severity,
                    "notes": self.governance.decrypt(l.notes_encrypted) if l.notes_encrypted else ""
                })
            return results
        finally:
            db.close()

    def log_medication(self, patient_id: str, name: str, dosage: str, frequency: str):
        """Record a new medication for a patient."""
        db = self._get_db()
        try:
            med = MedicationRecord(
                patient_id=patient_id,
                medication_name_encrypted=self.governance.encrypt(name),
                dosage_encrypted=self.governance.encrypt(dosage),
                frequency=frequency
            )
            db.add(med)
            db.commit()
            self.audit.log_change(patient_id, "PATIENT", "ADD_MEDICATION", f"Med#{name}", details={"frequency": frequency})
            return True
        finally:
            db.close()

    def get_medications(self, patient_id: str):
        """Retrieve active medications for a patient."""
        db = self._get_db()
        try:
            meds = db.query(MedicationRecord).filter(MedicationRecord.patient_id == patient_id, MedicationRecord.is_active == True).all()
            results = []
            for m in meds:
                results.append({
                    "id": m.id,
                    "name": self.governance.decrypt(m.medication_name_encrypted),
                    "dosage": self.governance.decrypt(m.dosage_encrypted),
                    "frequency": m.frequency,
                    "start_date": m.start_date.isoformat()
                })
            return results
        finally:
            db.close()

