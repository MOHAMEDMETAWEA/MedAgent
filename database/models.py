"""
Database Models - Enhanced for Feedback, Human Review, and Self-Improvement.
"""
import datetime
import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Boolean, Enum
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy import create_engine

Base = declarative_base()

class ReviewStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FLAGGED = "flagged"

class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin" # Developer
    SYSTEM = "system" # Internal Agent

class FeedbackRating(int, enum.Enum):
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, index=True)
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    status = Column(String)
    is_anonymized = Column(Boolean, default=False)
    language = Column(String, default="en") # en or ar
    
    logs = relationship("SystemLog", back_populates="session")
    interactions = relationship("Interaction", back_populates="session")
    feedback = relationship("UserFeedback", back_populates="session")

class MedicalCase(Base):
    """Groups related interactions into a single medical case."""
    __tablename__ = "medical_cases"
    
    id = Column(String, primary_key=True) # UUID
    user_id = Column(String, ForeignKey("user_accounts.id"))
    title = Column(String) # Short summary or main symptom
    status = Column(String, default="open") # open, closed
    risk_score = Column(Integer, default=0) # 0-100
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    interactions = relationship("Interaction", back_populates="case")

class Interaction(Base):
    __tablename__ = "interactions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("user_sessions.id"))
    case_id = Column(String, ForeignKey("medical_cases.id"), nullable=True) # Linked to a specific case
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    user_input_encrypted = Column(Text)
    diagnosis_output_encrypted = Column(Text)
    final_response_encrypted = Column(Text)
    language = Column(String, default="en")
    
    metadata_json = Column(JSON) 
    safety_flags = Column(JSON)
    
    # Review Workflow
    requires_human_review = Column(Boolean, default=False)
    review_status = Column(Enum(ReviewStatus), default=ReviewStatus.APPROVED) # Auto-approved unless flagged
    reviewer_comment = Column(Text, nullable=True)
    
    session = relationship("UserSession", back_populates="interactions")
    case = relationship("MedicalCase", back_populates="interactions")

class UserFeedback(Base):
    __tablename__ = "user_feedback"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("user_sessions.id"))
    interaction_id = Column(Integer, ForeignKey("interactions.id"), nullable=True)
    rating = Column(Integer) # 1-5
    comment = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    session = relationship("UserSession", back_populates="feedback")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    actor_id = Column(String)
    role = Column(String)
    action = Column(String)
    resource_target = Column(String)
    status = Column(String)
    ip_address = Column(String, nullable=True)

class SystemLog(Base):
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    level = Column(String) 
    component = Column(String)
    message = Column(Text)
    details = Column(JSON)
    session_id = Column(String, ForeignKey("user_sessions.id"), nullable=True)
    
    session = relationship("UserSession", back_populates="logs")

class PatientProfile(Base):
    __tablename__ = "patient_profiles"
    
    id = Column(String, primary_key=True) # user_id
    name_encrypted = Column(Text, nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    medical_history_encrypted = Column(Text, nullable=True) # JSON list of conditions/meds
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    reports = relationship("MedicalReport", back_populates="patient")

class MedicalReport(Base):
    __tablename__ = "medical_reports"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String, ForeignKey("patient_profiles.id"))
    session_id = Column(String, ForeignKey("user_sessions.id"))
    
    # Content Columns
    report_content_encrypted = Column(Text) # The full JSON/Text report
    report_type = Column(String, default="comprehensive")
    language = Column(String, default="en")
    
    # Versioning & Status
    version = Column(Integer, default=1)
    status = Column(Enum(ReviewStatus), default=ReviewStatus.PENDING)
    generated_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    patient = relationship("PatientProfile", back_populates="reports")
    session = relationship("UserSession")

class UserAccount(Base):
    """Core user identity and authentication data."""
    __tablename__ = "user_accounts"
    
    id = Column(String, primary_key=True) # UUID or unique username
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String, unique=True, index=True)
    full_name_encrypted = Column(Text)
    password_hash = Column(String)
    
    role = Column(Enum(UserRole), default=UserRole.USER)
    language_preference = Column(String, default="en")
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    account_status = Column(String, default="active") # active, suspended, deleted
    
    # Metadata for optional fields (encrypted JSON)
    profile_metadata_encrypted = Column(Text) 

class UserActivity(Base):
    """Tracks login/logout and session activity."""
    __tablename__ = "user_activities"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("user_accounts.id"))
    session_id = Column(String)
    login_time = Column(DateTime, default=datetime.datetime.utcnow)
    logout_time = Column(DateTime, nullable=True)
    ip_address = Column(String, nullable=True)
    status = Column(String) # success, failed, lockout

class SystemConfig(Base):
    __tablename__ = "system_config"
    key = Column(String, primary_key=True)
    value = Column(String) 
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_by = Column(String)

class UserAction(Base):
    """Tracks granular UI actions (clicks, views, etc.)"""
    __tablename__ = "user_actions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("user_sessions.id"))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    action_type = Column(String) # CLICK, VIEW, SELECT, EXPORT
    element_id = Column(String)  # UI button id or feature name
    details = Column(JSON)       # Additional context (e.g. which report, which language)
    
    version = Column(String, default="5.0.0") # MedAgent version
    audit_tag = Column(String)   # Tag for auditing (e.g. "SECURITY", "UX")
    
    session = relationship("UserSession")

class MedicalImage(Base):
    """Stores metadata and analysis for user-uploaded medical images."""
    __tablename__ = "medical_images"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("user_sessions.id"))
    patient_id = Column(String, ForeignKey("patient_profiles.id"), nullable=True)
    
    # Storage details
    image_path_encrypted = Column(Text) # Path to the stored local image (encrypted)
    original_filename = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Analysis results
    visual_findings_encrypted = Column(Text)
    possible_conditions_json = Column(JSON)
    confidence_score = Column(Integer) # Percentage 0-100 or 0.0-1.0
    severity_level = Column(String)    # low, moderate, high
    requires_human_review = Column(Boolean, default=False)
    
    session = relationship("UserSession")

class MemoryNode(Base):
    """Nodes for the User Memory Graph."""
    __tablename__ = "memory_nodes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("user_accounts.id"))
    node_type = Column(String) # Symptom, Diagnosis, Image, Report, Medication, Case
    content_encrypted = Column(Text)
    metadata_json = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class MemoryEdge(Base):
    """Edges for the User Memory Graph."""
    __tablename__ = "memory_edges"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("user_accounts.id"))
    source_node_id = Column(Integer, ForeignKey("memory_nodes.id"))
    target_node_id = Column(Integer, ForeignKey("memory_nodes.id"))
    relation_type = Column(String) # relates_to, caused_by, diagnosed_as, follow_up_of, based_on
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Medication(Base):
    """Tracks patient medications."""
    __tablename__ = "medications"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("user_accounts.id"))
    name_encrypted = Column(Text)
    dosage_encrypted = Column(Text)
    frequency_encrypted = Column(Text)
    start_date = Column(DateTime, default=datetime.datetime.utcnow)
    end_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    reminders = relationship("Reminder", back_populates="medication")

class Reminder(Base):
    """Tracks medication or appointment reminders."""
    __tablename__ = "reminders"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("user_accounts.id"))
    medication_id = Column(Integer, ForeignKey("medications.id"), nullable=True)
    title_encrypted = Column(Text)
    reminder_time = Column(Text) # Cron or ISO string
    is_enabled = Column(Boolean, default=True)
    last_triggered = Column(DateTime, nullable=True)
    
    medication = relationship("Medication", back_populates="reminders")

def init_db(db_url="sqlite:///./medagent.db"):
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)

SessionLocal = init_db()
