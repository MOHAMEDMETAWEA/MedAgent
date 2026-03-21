"""
Centralized Audit Logger for medical AI decisions.
Ensures every agent execution is traceable and compliant.
"""

import datetime
import hashlib
import json
import logging

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
        risk_level: str = "Low",
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
                    previous_hash=prev_hash,  # Cycle 5: Immutable Chain
                    timestamp=datetime.datetime.utcnow(),
                )

                db.add(log_entry)
                db.commit()
                logger.info(
                    f"Audit chain updated for {agent_name} (Link: {audit_hash[:8]}...)"
                )

        except Exception as e:
            logger.error(f"Failed to generate audit log: {e}")

    @staticmethod
    def export_fhir_audit_event(log_id: int) -> dict:
        """Transforms a standard audit log into a HL7 FHIR AuditEvent resource."""
        try:
            with SessionLocal() as db:
                log = db.query(AIAuditLog).filter(AIAuditLog.id == log_id).first()
                if not log:
                    return {"error": "Audit log not found"}

                return {
                    "resourceType": "AuditEvent",
                    "id": str(log.id),
                    "type": {
                        "system": "http://dicom.nema.org/resources/ontology/DCM",
                        "code": "110113",
                        "display": "Provisioning Event",
                    },
                    "action": "E",  # Execute
                    "recorded": log.timestamp.isoformat() + "Z",
                    "outcome": "0",  # Success
                    "agent": [
                        {
                            "type": {
                                "coding": [
                                    {
                                        "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
                                        "code": "AUT",
                                        "display": "Author",
                                    }
                                ]
                            },
                            "who": {"display": f"MedAgent {log.agent_name}"},
                            "requestor": True,
                        }
                    ],
                    "source": {
                        "observer": {
                            "display": "MedAgent Global Clinical Command Center"
                        }
                    },
                    "entity": [
                        {
                            "type": {
                                "system": "http://terminology.hl7.org/CodeSystem/audit-entity-type",
                                "code": "2",
                                "display": "System Object",
                            },
                            "description": f"AI Decision: {log.output_summary[:100]}",
                        }
                    ],
                }
        except Exception as e:
            logger.error(f"Failed to export FHIR AuditEvent: {e}")
            return {"error": str(e)}
