import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class NotificationEngine:
    """
    Unified Hospital Notification Engine
    - Merged: utils/notifications.py + notifications/engine.py
    Responsibilities:
    - Dispatch multi-channel alerts (Email, SMS, Push).
    - SMTP integration with HTML templates.
    - iCal appointment generation.
    - Emergency medical escalation logic.
    """
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("SMTP_FROM_EMAIL", "noreply@medagent.hospital")
        self.enabled = bool(self.smtp_host and self.smtp_user)
        
        self.priority_map = {"EMERGENCY": 1, "URGENT": 2, "ROUTINE": 3}

    async def send_alert(self, user_id: str, title: str, message: str, priority: str = "ROUTINE", email: str = None):
        """Dispatches an alert through the most appropriate channels."""
        logger.info(f"Notification: Dispatching '{title}' to {user_id} [Priority: {priority}]")
        
        # 1. Always Log & Push (Simulated)
        logger.info(f"[PUSH/SMS] {title}: {message}")
        
        # 2. If Emergency, Trigger Escalation
        if priority == "EMERGENCY":
            logger.critical(f"HEALTH-CRITICAL: Emergency escalation triggered for {user_id}")
            
        # 3. If email provided, send SMTP
        if email:
            self._send_formatted_email(email, title, message, priority)

    def _send_formatted_email(self, to_email: str, title: str, message: str, priority: str):
        """Sends a rich HTML email based on priority."""
        if not self.enabled:
            logger.info(f"[EMAIL-SIMULATED] To: {to_email} | Subject: {title}")
            return True

        # Simplified HTML template logic from legacy utils/notifications.py
        color = "#c62828" if priority == "EMERGENCY" else "#1565c0"
        body_html = f"""
        <div style="font-family: sans-serif; max-width: 600px; border: 1px solid #eee;">
            <div style="background: {color}; color: white; padding: 20px; text-align: center;">
                <h2>{title}</h2>
            </div>
            <div style="padding: 20px;">
                <p>{message}</p>
                <hr>
                <p style="font-size: 12px; color: #999;">Automated Clinical Alert - MEDAgent Hospital System</p>
            </div>
        </div>
        """
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = title
            msg["From"] = self.from_email
            msg["To"] = to_email
            msg.attach(MIMEText(body_html, "html"))
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            return True
        except Exception as e:
            logger.error(f"SMTP Failed: {e}")
            return False

    def generate_ical(self, title: str, start_time: datetime, duration: int = 30) -> str:
        """Utility for clinical appointment integration."""
        end_time = start_time + timedelta(minutes=duration)
        return f"BEGIN:VCALENDAR\nSUMMARY:{title}\nDTSTART:{start_time.isoformat()}\nDTEND:{end_time.isoformat()}\nEND:VCALENDAR"

# Singleton Instance
notification_engine = NotificationEngine()
