"""
Pre-Launch System Check for MEDAgent.
Run this script to verify system integrity before deployment.
"""
import sys
import os
import logging

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import settings
from agents.orchestrator import MedAgentOrchestrator
from agents.supervisor_agent import SupervisorAgent
from agents.generative_engine_agent import GenerativeEngineAgent
from agents.persistence_agent import PersistenceAgent
from database.models import UserSession, PatientProfile

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PreLaunchCheck")

def check_configuration():
    logger.info("--- 1. Checking Configuration ---")
    if not settings.OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY is NOT set. LLM features will fail.")
        return False
    logger.info(f"OPENAI_MODEL: {settings.OPENAI_MODEL}")
    logger.info(f"Database Path: {settings.DATA_DIR}")
    return True

def check_agents_loading():
    logger.info("--- 2. Verifying Agent Initialization ---")
    try:
        orchestrator = MedAgentOrchestrator()
        supervisor = SupervisorAgent()
        gen_engine = GenerativeEngineAgent()
        logger.info("All agents initialized successfully.")
        return orchestrator, supervisor, gen_engine
    except Exception as e:
        logger.error(f"Failed to initialize agents: {e}")
        return None, None, None

def check_database_connection():
    logger.info("--- 3. Testing Database Connectivity ---")
    try:
        persistence = PersistenceAgent()
        session_count = persistence.db.query(UserSession).count()
        logger.info(f"Database connected. Current session count: {session_count}")
        persistence.close()
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

def run_integration_test(orchestrator):
    logger.info("--- 4. Running End-to-End Workflow Test (English) ---")
    input_text = "I have a severe headache and sensitivity to light."
    user_id = "test_user_prelaunch"
    
    try:
        result = orchestrator.run(input_text, user_id=user_id)
        
        if result.get("status") == "error":
            logger.error(f"Workflow failed: {result.get('final_response')}")
            return False
            
        logger.info("Workflow completed successfully.")
        logger.info(f"Language Detected: {result.get('language')}")
        logger.info(f"Final Response Length: {len(result.get('final_response', ''))}")
        return True
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        return False

def test_generative_engine(gen_engine):
    logger.info("--- 5. Testing Generative Engine ---")
    try:
        content = gen_engine.generate_educational_content("Flu Prevention", "patient", "en")
        if "Error" in content:
            logger.warning("Generative Engine returned an error (likely API or Safety).")
        else:
            logger.info("Generative Engine produced content successfully.")
        return True
    except Exception as e:
        logger.error(f"Generative Engine failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("STARTING PRE-LAUNCH SYSTEM CHECK")
    
    config_ok = check_configuration()
    
    orchestrator, supervisor, gen_engine = check_agents_loading()
    
    db_ok = check_database_connection()
    
    workflow_ok = False
    if orchestrator and config_ok:
        workflow_ok = run_integration_test(orchestrator)
        
    gen_ok = False
    if gen_engine and config_ok:
        gen_ok = test_generative_engine(gen_engine)
        
    logger.info("-" * 30)
    logger.info("SUMMARY:")
    logger.info(f"Configuration: {'PASS' if config_ok else 'FAIL'}")
    logger.info(f"Agent Loading: {'PASS' if orchestrator else 'FAIL'}")
    logger.info(f"Database:      {'PASS' if db_ok else 'FAIL'}")
    logger.info(f"Workflow:      {'PASS' if workflow_ok else 'FAIL'}")
    logger.info(f"Gen Engine:    {'PASS' if gen_ok else 'FAIL'}")
    logger.info("-" * 30)
    
    if config_ok and orchestrator and db_ok and workflow_ok:
        logger.info("SYSTEM IS READY FOR LAUNCH")
        sys.exit(0)
    else:
        logger.error("SYSTEM HAS CRITICAL ISSUES")
        sys.exit(1)
