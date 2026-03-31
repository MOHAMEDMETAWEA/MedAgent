"""
Audit Agent - Centralized specialized auditing for all system changes.
Tracks data mutations, security events, and administrative actions.
"""

import logging
from datetime import datetime

from database.models import AuditLog, SessionLocal

logger = logging.getLogger(__name__)


class AuditAgent:
    """
    Centralized agent for recording and managing audit trails.
    """

    def __init__(self):
        self._db_factory = SessionLocal

    def log_change(
        self,
        actor_id: str,
        role: str,
        action: str,
        resource: str,
        status: str = "SUCCESS",
        details: dict = None,
        ip: str = None,
    ):
        """
        Record a significant change or update in the system.
        :param actor_id: ID of the user or system component performing the action.
        :param role: Role of the actor.
        :param action: The action performed (e.g., 'UPDATE_USER', 'EXPORT_REPORT').
        :param resource: The resource affected (e.g., 'User#123', 'Report#45').
        :param status: Result of the action ('SUCCESS', 'FAILURE').
        :param details: Dictionary of specific changes (e.g., {'old': '...', 'new': '...'}).
        :param ip: IP address of the requester.
        """
        db = self._db_factory()
        try:
            audit = AuditLog(
                actor_id=actor_id,
                role=role,
                action=action,
                resource_target=resource,
                status=status,
                details=details or {},
                ip_address=ip,
            )
            db.add(audit)
            db.commit()
            logger.info(f"Audit log created: {action} on {resource} by {actor_id}")
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            db.rollback()
        finally:
            db.close()

    def get_logs(self, limit: int = 100, actor_id: str = None):
        """Retrieve audit logs with optional filtering. Returns serializable dicts."""
        db = self._db_factory()
        try:
            query = db.query(AuditLog)
            if actor_id:
                query = query.filter(AuditLog.actor_id == actor_id)
            logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
            results = []
            for log in logs:
                results.append(
                    {
                        "id": log.id,
                        "timestamp": log.timestamp.isoformat() if log.timestamp else "",
                        "actor_id": log.actor_id,
                        "role": log.role,
                        "action": log.action,
                        "resource_target": log.resource_target,
                        "status": log.status,
                        "details": log.details or {},
                        "ip_address": log.ip_address,
                    }
                )
            return results
        finally:
            db.close()
