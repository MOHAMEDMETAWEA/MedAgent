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

class Interaction(Base):
    __tablename__ = "interactions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("user_sessions.id"))
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

class SystemConfig(Base):
    __tablename__ = "system_config"
    key = Column(String, primary_key=True)
    value = Column(String) 
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_by = Column(String)

def init_db(db_url="sqlite:///./medagent.db"):
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)

SessionLocal = init_db()
