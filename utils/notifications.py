"""
Notification & Reminder Service for MedAgent.
Supports: Email (SMTP), iCal export, and system logging of notifications.
"""
import smtplib
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class NotificationService:
    """Centralized notification dispatcher."""

    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("SMTP_FROM_EMAIL", "noreply@medagent.local")
        self.enabled = bool(self.smtp_host and self.smtp_user)
        if not self.enabled:
            logger.warning("SMTP not configured — email notifications disabled. Set SMTP_HOST, SMTP_USER, SMTP_PASSWORD.")

    def send_email(self, to_email: str, subject: str, body_html: str, body_text: str = "") -> bool:
        """Send an email notification via SMTP."""
        if not self.enabled:
            logger.info(f"[NOTIFICATION-SIMULATED] To: {to_email} | Subject: {subject}")
            return True  # Simulate success when SMTP not configured

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = to_email

            if body_text:
                msg.attach(MIMEText(body_text, "plain"))
            msg.attach(MIMEText(body_html, "html"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            logger.info(f"Email sent to {to_email}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return False

    def send_appointment_confirmation(self, to_email: str, appointment_time: str, title: str = "Medical Appointment"):
        """Send appointment confirmation email."""
        subject = f"MedAgent — Appointment Confirmed: {title}"
        body_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #2e7d32; color: white; padding: 20px; text-align: center;">
                <h2>MedAgent Appointment Confirmed ✅</h2>
            </div>
            <div style="padding: 20px; background: #f9f9f9;">
                <h3>{title}</h3>
                <p><strong>Time:</strong> {appointment_time}</p>
                <p><strong>Location:</strong> Online / Clinic</p>
                <hr>
                <p style="color: #666; font-size: 12px;">
                    This is an automated notification from MedAgent. Do not reply to this email.
                </p>
            </div>
        </div>
        """
        return self.send_email(to_email, subject, body_html)

    def send_medication_reminder(self, to_email: str, med_name: str, dosage: str, frequency: str):
        """Send medication reminder email."""
        subject = f"MedAgent — Medication Reminder: {med_name}"
        body_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #1565c0; color: white; padding: 20px; text-align: center;">
                <h2>💊 Medication Reminder</h2>
            </div>
            <div style="padding: 20px; background: #f9f9f9;">
                <h3>{med_name}</h3>
                <p><strong>Dosage:</strong> {dosage}</p>
                <p><strong>Frequency:</strong> {frequency}</p>
                <p>Please take your medication as prescribed.</p>
                <hr>
                <p style="color: #666; font-size: 12px;">
                    This is an automated reminder from MedAgent.
                </p>
            </div>
        </div>
        """
        return self.send_email(to_email, subject, body_html)

    def send_report_ready(self, to_email: str, report_id: int):
        """Notify user that their medical report is ready."""
        subject = "MedAgent — Your Medical Report is Ready"
        body_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #2e7d32; color: white; padding: 20px; text-align: center;">
                <h2>📋 Report Ready</h2>
            </div>
            <div style="padding: 20px; background: #f9f9f9;">
                <p>Your medical report (ID: #{report_id}) has been generated.</p>
                <p>Log in to MedAgent to view, download as PDF/Image, or share.</p>
            </div>
        </div>
        """
        return self.send_email(to_email, subject, body_html)

    def send_risk_alert(self, to_email: str, risk_details: str):
        """Send high-risk medical alert."""
        subject = "🚨 MedAgent — Abnormal Medical Risk Detected"
        body_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #c62828; color: white; padding: 20px; text-align: center;">
                <h2>🚨 URGENT: Risk Alert</h2>
            </div>
            <div style="padding: 20px; background: #fff3f3;">
                <p>{risk_details}</p>
                <p><strong>Please seek immediate medical attention.</strong></p>
            </div>
        </div>
        """
        return self.send_email(to_email, subject, body_html)


def generate_ical_event(title: str, start_time: datetime, duration_minutes: int = 30,
                         description: str = "", location: str = "Online / Clinic") -> str:
    """Generate an iCal (.ics) formatted string for an appointment."""
    end_time = start_time + timedelta(minutes=duration_minutes)
    now = datetime.utcnow()

    def fmt(dt):
        return dt.strftime("%Y%m%dT%H%M%SZ")

    return f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//MedAgent//Medical Appointments//EN
BEGIN:VEVENT
DTSTART:{fmt(start_time)}
DTEND:{fmt(end_time)}
DTSTAMP:{fmt(now)}
SUMMARY:{title}
DESCRIPTION:{description}
LOCATION:{location}
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR"""


# Singleton
_notification_service = None

def get_notification_service() -> NotificationService:
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
