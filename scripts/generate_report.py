"""
Governance Reporting Script.
Generates a structured report on System Health, Security, and Data Governance.
"""
import sys
import logging
from agents.governance_agent import GovernanceAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Reporter")

def generate_report():
    gov = GovernanceAgent()
    
    print("--------------------------------------------------")
    print("MEDAGENT SYSTEM GOVERNANCE REPORT")
    print("--------------------------------------------------")
    
    # 1. System Health
    try:
        gov.db.execute("SELECT 1")
        print("[PASS] Database Connectivity: OK")
    except Exception as e:
        print(f"[FAIL] Database Connectivity: ERROR ({e})")
        
    # 2. Encryption Check
    test_str = "sensitive_data"
    enc = gov.encrypt(test_str)
    dec = gov.decrypt(enc)
    if dec == test_str:
        print("[PASS] Encryption/Decryption: ACTIVE")
    else:
        print("[FAIL] Encryption Logic: BROKEN")

    # 3. Compliance & Retention
    # Check config
    retention = gov.get_config("retention_policy_days", 30)
    print(f"[INFO] Data Retention Policy: {retention} Days")
    
    print("--------------------------------------------------")
    print("Report Generated Successfully.")
    print("--------------------------------------------------")

if __name__ == "__main__":
    generate_report()
