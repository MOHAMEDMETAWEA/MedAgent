import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append("d:\\MedAgent")

from database.models import AuditLog, SessionLocal, SystemLog


def verify_logs():
    db = SessionLocal()
    try:
        sys_logs = db.query(SystemLog).count()
        audit_logs = db.query(AuditLog).count()

        print(f"System Logs Count: {sys_logs}")
        print(f"Audit Logs Count: {audit_logs}")

        if sys_logs > 0 and audit_logs > 0:
            print("RESULT: PASS")
        else:
            print("RESULT: FAIL (No logs found)")
    finally:
        db.close()


if __name__ == "__main__":
    verify_logs()
