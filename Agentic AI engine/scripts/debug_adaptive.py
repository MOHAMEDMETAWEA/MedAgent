import os
import sys

sys.path.append(os.getcwd())

import logging

from agents.orchestrator import MedAgentOrchestrator

# Set logging to see what's happening
logging.basicConfig(level=logging.INFO)


def debug_consultation():
    orchestrator = MedAgentOrchestrator()

    # Simulate a patient consultation
    print("\n--- DEBUG: PATIENT CONSULTATION ---")
    result = orchestrator.run(
        initial_input="I have hypertension and chest pain.",
        user_id="guest",
        interaction_mode="patient",
    )
    print(f"Final Response: {result.get('final_response')}")

    # Simulate a doctor consultation with 'patient' mode override (Simplify)
    print("\n--- DEBUG: DOCTOR OVERRIDE (SIMPLIFY) ---")
    result_d = orchestrator.run(
        initial_input="Patient presenting with hypertension and chest pain.",
        user_id="guest",  # Using guest for simplicity in debug
        interaction_mode="patient",
    )
    print(f"Final Response (Simplified): {result_d.get('final_response')}")


if __name__ == "__main__":
    debug_consultation()
