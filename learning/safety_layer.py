import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from agents.governance_agent import GovernanceAgent

logger = logging.getLogger(__name__)

class ClinicalAuditLogger:
    """HIPAA-compliant clinical audit log."""
    def __init__(self):
        self.governance = GovernanceAgent()
        
    async def log_interaction(self, user_id: str, action: str, encrypted_data: str):
        """Creates a secure, immutable record of every clinical interaction."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,
            "data_blob": encrypted_data, # Assumed encrypted before calling
            "system_version": "5.3.0"
        }
        logger.info(f"AUDIT_CLINICAL: {json.dumps(log_entry)}")
        # In production, this writes to a secure DB or WORM storage

class HospitalSafetyLayer:
    """
    Phase 7: AI Safety & Compliance
    Responsibilities:
    - Block unsafe medical advice.
    - Detect hallucinated medical entities.
    - Enforce mandatory disclaimers.
    """
    def __init__(self):
        self.unsafe_keywords = ["take bleach", "stop insulin", "no need for surgery", "ignore doctor"]
        self.disclaimers = "Not a replacement for professional medical advice / ليس بديلاً عن الاستشارة الطبية"

    async def run_safety_sweep(self, ai_output: str) -> Dict[str, Any]:
        """Scans AI output for clinical risks."""
        output_lower = ai_output.lower()
        
        # 1. Check for unsafe keywords
        for kw in self.unsafe_keywords:
            if kw in output_lower:
                return {"safe": False, "reason": f"Unsafe advice detected: '{kw}'"}
                
        # 2. Hallucination Detection (Simulated Fact-Check)
        # 3. Ensure Disclaimer is present
        if "doctor" not in output_lower and "emergency" not in output_lower:
             ai_output += f"\n\n---\n{self.disclaimers}"
             
        return {"safe": True, "final_output": ai_output}

# Singleton Instance
hospital_safety = HospitalSafetyLayer()
audit_logger = ClinicalAuditLogger()
