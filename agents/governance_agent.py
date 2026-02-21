"""
Governance Agent - Managing Security, RBAC, and Data Integrity.
Handles encryption, audit logging, and admin controls.
"""
import os
import json
import base64
import logging
import jwt
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database.models import SessionLocal, AuditLog, SystemConfig, UserSession, Interaction, UserRole, UserAccount, UserActivity
from config import settings

logger = logging.getLogger(__name__)

class GovernanceAgent:
    """
    Enforces Data Governance policies: Encryption, RBAC, Auditing.
    """
    def __init__(self):
        self.db: Session = SessionLocal()
        # Initialize Encryption Key
        self._key = os.getenv("DATA_ENCRYPTION_KEY")
        if not self._key:
            # Generate a temporary one for demo if not set (Safe failsafe)
            self._key = Fernet.generate_key().decode()
            logger.warning("DATA_ENCRYPTION_KEY not set. Using temporary key. DATA WILL BE UNREADABLE AFTER RESTART.")
        self.cipher = Fernet(self._key.encode())
        
        # Password Hashing
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # JWT Config
        self.jwt_secret = os.getenv("JWT_SECRET_KEY", "medagent-super-secret-jwt-key")
        self.jwt_algorithm = "HS256"
        self.token_expire_minutes = 60 * 24 # 24 hours

    # --- ENCRYPTION ---
    def encrypt(self, data: str) -> str:
        if not data: return ""
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt(self, token: str) -> str:
        if not token: return ""
        try:
            return self.cipher.decrypt(token.encode()).decode()
        except:
            return "[ENCRYPTED_DATA_ERROR]"

    # --- AUTHENTICATION ---
    def hash_password(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.token_expire_minutes)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.jwt_secret, algorithm=self.jwt_algorithm)

    def verify_token(self, token: str):
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload # user_id, role, etc.
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    # --- AUDIT LOGGING ---
    def log_action(self, actor_id: str, role: str, action: str, target: str, status: str = "SUCCESS", ip: str = None):
        """Create an immutable audit record."""
        try:
            audit = AuditLog(
                actor_id=actor_id,
                role=role,
                action=action,
                resource_target=target,
                status=status,
                ip_address=ip
            )
            self.db.add(audit)
            self.db.commit()
        except Exception as e:
            logger.critical(f"AUDIT FAILURE: {e}")
            self.db.rollback()

    # --- RBAC ---
    def check_permission(self, role: str, action: str) -> bool:
        """Map roles to permissions."""
        # Simple policy map
        policy = {
            UserRole.USER: ["READ_OWN_HISTORY", "DELETE_OWN_DATA", "CONSULT"],
            UserRole.PATIENT: ["READ_OWN_HISTORY", "DELETE_OWN_DATA", "CONSULT"],
            UserRole.DOCTOR: ["READ_OWN_HISTORY", "DELETE_OWN_DATA", "CONSULT", "DOCTOR_TOOLS", "VIEW_CASE_STUDIES"],
            UserRole.ADMIN: ["READ_ALL_LOGS", "SYSTEM_CONFIG", "VIEW_ANALYTICS", "READ_OWN_HISTORY"],
            UserRole.SYSTEM: ["WRITE_LOGS", "READ_CONFIG"]
        }
        allowed = policy.get(role, [])
        if action in allowed:
            return True
        return False

    # --- DATA RETENTION & DELETION ---
    def anonymize_data(self, days_retention: int = 30):
        """Anonymize data older than X days (GDPR/Compliance)."""
        cutoff = datetime.utcnow() - timedelta(days=days_retention)
        try:
            sessions = self.db.query(UserSession).filter(
                UserSession.start_time < cutoff,
                UserSession.is_anonymized == False
            ).all()
            
            count = 0
            for s in sessions:
                s.user_id = "ANONYMIZED"
                s.is_anonymized = True
                # We might also wipe specific interaction text if required
                count += 1
            
            self.db.commit()
            self.log_action("SYSTEM", "SYSTEM", "AUTO_ANONYMIZE", f"{count}_records")
        except Exception as e:
            logger.error(f"Anonymization fail: {e}")

    def delete_user_data(self, user_id: str):
        """Right to be forgotten."""
        try:
            # We don't delete logs, but we delete PII sessions
            self.db.query(UserSession).filter(UserSession.user_id == user_id).delete()
            self.db.commit()
            self.log_action(user_id, "USER", "DELETE_ACCOUNT", "ALL_DATA")
            return True
        except Exception as e:
            logger.error(f"Delete user failed: {e}")
            return False

    # --- SYSTEM CONFIG ---
    def get_config(self, key: str, default=None):
        cfg = self.db.query(SystemConfig).filter(SystemConfig.key == key).first()
        if cfg:
            return json.loads(cfg.value)
        return default

    def set_config(self, key: str, value, actor_id: str):
        current = self.db.query(SystemConfig).filter(SystemConfig.key == key).first()
        val_str = json.dumps(value)
        if current:
            current.value = val_str
            current.updated_at = datetime.utcnow()
            current.updated_by = actor_id
        else:
            new_cfg = SystemConfig(key=key, value=val_str, updated_by=actor_id)
            self.db.add(new_cfg)
        self.db.commit()
        self.log_action(actor_id, "ADMIN", "UPDATE_CONFIG", key)

    def close(self):
        self.db.close()
