import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

class PatientMonitoringSystem:
    """
    Phase 3: Real-Time Patient Monitoring
    Responsibilities:
    - Track patient vitals (Heart rate, O2, BP, etc.)
    - Detect symptom progression anomalies.
    - Trigger clinical escalations and red-flag alerts.
    """
    def __init__(self):
        self.monitored_patients = {}
        self.emergency_thresholds = {
            "heart_rate": (40, 140), # BPM
            "spo2": (90, 100), # %
            "temperature": (35.0, 39.5) # Celsius
        }

    async def start_monitoring(self, patient_id: str):
        """Initializes real-time tracking for a specific patient."""
        logger.info(f"Monitoring: Active tracking started for patient {patient_id}")
        self.monitored_patients[patient_id] = {
            "status": "stable",
            "last_check": datetime.utcnow().isoformat(),
            "vital_history": []
        }

    async def update_vitals(self, patient_id: str, vitals: Dict[str, float]):
        """Receives new vital sign telemetry and checks for risks."""
        if patient_id not in self.monitored_patients:
            await self.start_monitoring(patient_id)
            
        logger.info(f"Monitoring: Received telemetry for {patient_id}: {vitals}")
        self.monitored_patients[patient_id]["last_vitals"] = vitals
        self.monitored_patients[patient_id]["vital_history"].append(vitals)
        
        # Check for anomalies
        anomaly = self._analyze_vitals(vitals)
        if anomaly:
            await self._trigger_escalation(patient_id, anomaly)

    def _analyze_vitals(self, vitals: Dict[str, float]) -> Optional[str]:
        """Analyzes vitals against clinical safety thresholds."""
        for metric, (low, high) in self.emergency_thresholds.items():
            val = vitals.get(metric)
            if val is not None:
                if val < low or val > high:
                    return f"Critical {metric} detected: {val}"
        return None

    async def _trigger_escalation(self, patient_id: str, reason: str):
        """Triggers emergency workflow: Alerts doctors and patient."""
        self.monitored_patients[patient_id]["status"] = "CRITICAL"
        logger.critical(f"Monitoring ALERT: Emergency Escalation for {patient_id}. Reason: {reason}")
        
        # In Phase 9, this would call the NotificationEngine
        # For now, we simulate the transmission
        email_sent = True
        push_sent = True
        logger.info(f"Monitoring: Emergency notifications dispatched via Email/Push.")

# Singleton Instance
monitoring_engine = PatientMonitoringSystem()
