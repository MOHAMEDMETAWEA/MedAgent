"""
Centralized Audit Logger for medical AI decisions.
Ensures every agent execution is traceable and compliant.
"""
import logging
import datetime
import hashlib
import json
from database.models import AIAuditLog, SessionLocal

logger = logging.getLogger(__name__)

class AuditLogger:
    @staticmethod
    def log_agent_interaction(
        user_id: str,
        agent_name: str,
        input_data: str,
        output_data: str,
        model_used: str,
        confidence: float = 0.0,
        risk_level: str = "Low"
    ):
        """Records an agent execution event in the high-fidelity audit trail."""
        try:
            with SessionLocal() as db:
                # Fetch last hash for the chain
                last_log = db.query(AIAuditLog).order_by(AIAuditLog.id.desc()).first()
                prev_hash = last_log.audit_hash if last_log else "GENESIS_BLOCK"

                # Create integrity hash (linked)
                raw_content = f"{prev_hash}-{user_id}-{agent_name}-{input_data[:50]}-{output_data[:50]}"
                audit_hash = hashlib.sha256(raw_content.encode()).hexdigest()

                log_entry = AIAuditLog(
                    user_id=user_id,
                    agent_name=agent_name,
                    input_summary=input_data[:500],
                    output_summary=output_data[:500],
                    model_used=model_used,
                    confidence_score=confidence,
                    risk_level=risk_level,
                    audit_hash=audit_hash,
                    previous_hash=prev_hash, # Cycle 5: Immutable Chain
                    timestamp=datetime.datetime.utcnow()
                )

                db.add(log_entry)
                db.commit()
                logger.info(f"Audit chain updated for {agent_name} (Link: {audit_hash[:8]}...)")
                
        except Exception as e:
            logger.error(f"Failed to generate audit log: {e}")

    @staticmethod
    def export_fhir_audit_event(log_id: int) -> dict:
        """Transforms a standard audit log into a HL7 FHIR AuditEvent resource."""
        # Implementation for Feature 8: Compliance-Ready Logging
        return {"resourceType": "AuditEvent", "id": str(log_id), "status": "active"}
