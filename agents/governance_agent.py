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
import hmac
import hashlib

logger = logging.getLogger(__name__)

class GovernanceAgent:
    """
    Enforces Data Governance policies: Encryption, RBAC, Auditing.
    """
    def __init__(self):
        self._db_factory = SessionLocal
        # Initialize Encryption Key
        self._key = os.getenv("DATA_ENCRYPTION_KEY")
        if not self._key:
            # Generate a temporary one for demo if not set (Safe failsafe)
            self._key = Fernet.generate_key().decode()
            logger.warning("DATA_ENCRYPTION_KEY not set. Using temporary key. DATA WILL BE UNREADABLE AFTER RESTART.")
        self.cipher = Fernet(self._key.encode())
        
        # Password Hashing
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # JWT Config (must be provided via env)
        self.jwt_secret = os.getenv("JWT_SECRET_KEY") or getattr(settings, "JWT_SECRET_KEY", None)
        self.jwt_algorithm = "HS256"
        self.token_expire_minutes = 60 * 24 # 24 hours
        if not self.jwt_secret:
            logger.critical("JWT_SECRET_KEY is not set. Refusing to operate without a secure JWT secret.")
            raise RuntimeError("JWT secret missing")

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
        import uuid
        jti = str(uuid.uuid4())
        to_encode.update({"jti": jti}) # Added for revocation tracking
        
        for key, val in to_encode.items():
            if hasattr(val, 'value'):
                to_encode[key] = val.value
        expire = datetime.utcnow() + timedelta(minutes=self.token_expire_minutes)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.jwt_secret, algorithm=self.jwt_algorithm)

    def verify_token(self, token: str):
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            # Security Hardening: Check Redis Blacklist
            jti = payload.get("jti")
            if jti:
                from intelligence.inference_cache import inference_cache
                if inference_cache._enabled:
                    if inference_cache._redis.exists(f"token_blacklist:{jti}"):
                        logger.warning(f"SECURITY: Blocked attempt to use revoked token {jti}")
                        return None
            
            return payload 
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def revoke_token(self, token: str):
        """Standard Logout: Add token to blacklist until it expires."""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            jti = payload.get("jti")
            exp = payload.get("exp")
            if jti and exp:
                from intelligence.inference_cache import inference_cache
                if inference_cache._enabled:
                    # TTL = time remaining until expiration
                    ttl = int(exp - datetime.utcnow().timestamp())
                    if ttl > 0:
                        inference_cache._redis.setex(f"token_blacklist:{jti}", ttl, "revoked")
                        logger.info(f"SECURITY: Token {jti} revoked.")
            return True
        except:
            return False

    # --- AUDIT LOGGING ---
    def log_action(self, actor_id: str, role: str, action: str, target: str, status: str = "SUCCESS", details: dict = None, ip: str = None):
        """Create an immutable audit record."""
        db = self._db_factory()
        try:
            audit = AuditLog(
                actor_id=actor_id,
                role=role,
                action=action,
                resource_target=target,
                status=status,
                details=details or {},
                ip_address=ip
            )
            db.add(audit)
            db.commit()
        except Exception as e:
            logger.critical(f"AUDIT FAILURE: {e}")
            db.rollback()
        finally:
            db.close()

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
        db = self._db_factory()
        try:
            sessions = db.query(UserSession).filter(
                UserSession.start_time < cutoff,
                UserSession.is_anonymized == False
            ).all()
            
            count = 0
            for s in sessions:
                s.user_id = "ANONYMIZED"
                s.is_anonymized = True
                count += 1
            
            db.commit()
            self.log_action("SYSTEM", "SYSTEM", "AUTO_ANONYMIZE", f"{count}_records")
        except Exception as e:
            logger.error(f"Anonymization fail: {e}")
        finally:
            db.close()

    def delete_user_data(self, user_id: str):
        """Right to be forgotten."""
        db = self._db_factory()
        try:
            db.query(UserSession).filter(UserSession.user_id == user_id).delete()
            db.commit()
            self.log_action(user_id, "USER", "DELETE_ACCOUNT", "ALL_DATA")
            return True
        except Exception as e:
            logger.error(f"Delete user failed: {e}")
            return False
        finally:
            db.close()

    # --- SYSTEM CONFIG ---
    def get_config(self, key: str, default=None):
        db = self._db_factory()
        try:
            cfg = db.query(SystemConfig).filter(SystemConfig.key == key).first()
            if cfg:
                return json.loads(cfg.value)
            return default
        finally:
            db.close()

    def set_config(self, key: str, value, actor_id: str):
        db = self._db_factory()
        try:
            current = db.query(SystemConfig).filter(SystemConfig.key == key).first()
            val_str = json.dumps(value)
            if current:
                current.value = val_str
                current.updated_at = datetime.utcnow()
                current.updated_by = actor_id
            else:
                new_cfg = SystemConfig(key=key, value=val_str, updated_by=actor_id)
                db.add(new_cfg)
            db.commit()
            self.log_action(actor_id, "ADMIN", "UPDATE_CONFIG", key)
        finally:
            db.close()

    def close(self):
        pass  # No persistent session to close

    # --- AUDIT EVIDENCE SIGNING ---
    def sign_evidence(self, payload: str) -> str:
        """
        Create HMAC-SHA256 signature for evidence payload using AUDIT_SIGNING_KEY.
        """
        key = os.getenv("AUDIT_SIGNING_KEY") or getattr(settings, "AUDIT_SIGNING_KEY", None)
        if not key:
            raise RuntimeError("AUDIT_SIGNING_KEY not configured")
        sig = hmac.new(key.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
        return sig
