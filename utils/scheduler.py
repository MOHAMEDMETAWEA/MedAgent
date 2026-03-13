import time
import threading
import logging
import datetime
from agents.persistence_agent import PersistenceAgent
from utils.notifications import get_notification_service

logger = logging.getLogger(__name__)

class MedicationScheduler:
    """
    Lightweight background worker to handle medication reminders.
    Polls the database and dispatches notifications.
    """
    def __init__(self, interval_seconds=60):
        self.interval = interval_seconds
        self.persistence = PersistenceAgent()
        self.notifier = get_notification_service()
        self.running = False
        self._thread = None

    def start(self):
        if not self.running:
            self.running = True
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
            logger.info("Medication Scheduler started.")

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=5)
            logger.info("Medication Scheduler stopped.")

    def _run(self):
        while self.running:
            try:
                self._check_reminders()
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
            time.sleep(self.interval)

    def _check_reminders(self):
        active_rems = self.persistence.get_all_active_reminders()
        now = datetime.datetime.utcnow()
        
        for rem in active_rems:
            # Simple check: if reminder_time (e.g. "08:00") matches current time
            # and wasn't triggered in the last 12 hours.
            try:
                rem_time_str = rem["time"] # Expected "HH:MM" or similar
                if ":" in rem_time_str:
                    h, m = map(int, rem_time_str.split(":"))
                    if now.hour == h and now.minute == m:
                        # Check last trigger
                        last = rem["last_triggered"]
                        if not last or (now - last).total_seconds() > 3600: # 1 hour grace
                            self._trigger_reminder(rem)
            except Exception as e:
                logger.warning(f"Error parsing reminder time '{rem['time']}': {e}")

    def _trigger_reminder(self, rem):
        logger.info(f"Triggering reminder: {rem['title']} for {rem['email']}")
        try:
            success = self.notifier.send_email(
                rem["email"],
                f"MedAgent Reminder: {rem['title']}",
                f"<div style='border-left: 5px solid #1565c0; padding: 15px; background: #f1f5f9;'>"
                f"<h3>🔔 Medication Reminder</h3>"
                f"<p>It is time for your scheduled reminder: <b>{rem['title']}</b></p>"
                f"<p>Scheduled Time: {rem['time']}</p>"
                f"<hr><p style='font-size: 10px; color: #666;'>Sent by MedAgent Clinical Scheduler</p></div>"
            )
            if success:
                self.persistence.mark_reminder_triggered(rem["id"])
        except Exception as e:
            logger.error(f"Failed to trigger reminder {rem['id']}: {e}")

# Singleton
_scheduler = None

def start_scheduler():
    global _scheduler
    if _scheduler is None:
        _scheduler = MedicationScheduler()
        _scheduler.start()
    return _scheduler
