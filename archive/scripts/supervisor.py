"""
Supervisor Agent - Automated Monitoring & Health Checks.
Updated for Language and Self-Improvement Checks.
"""
import logging
import requests
from agents.persistence_agent import PersistenceAgent
from agents.self_improvement_agent import SelfImprovementAgent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - SUPERVISOR - %(levelname)s - %(message)s')
logger = logging.getLogger("Supervisor")

PERSISTENCE = PersistenceAgent()
IMPROVER = SelfImprovementAgent()

def run_supervisor_cycle():
    logger.info("--- STARTING SUPERVISOR CYCLE ---")
    
    # 1. API Health
    try:
        r = requests.get("http://localhost:8000/health", timeout=5)
        if r.status_code == 200:
            logger.info("API Health: PASS")
        else:
            logger.error(f"API Health: FAIL ({r.status_code})")
    except:
        logger.error("API Health: CONNECTION FAIL")

    # 2. Improvement Analysis (Run periodically)
    try:
        report = IMPROVER.generate_improvement_report()
        logger.info("Self-Improvement Analysis Complete")
        # Log if there are actionable items
        if "NEGATIVE" in report:
            PERSISTENCE.log_system_event("INFO", "Supervisor", "Negative Feedback Detected", {"summary": report[:100]})
    except Exception as e:
        logger.error(f"Improvement Analysis Fail: {e}")

    logger.info("--- SUPERVISOR CYCLE COMPLETE ---")

if __name__ == "__main__":
    run_supervisor_cycle()
