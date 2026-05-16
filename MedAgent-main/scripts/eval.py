import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

GOLD_SET_PATH = Path("data/gold/triage_eval.jsonl")

def load_gold_set(path: Path) -> list[dict]:
    if not path.exists():
        logger.error(f"Gold set not found at {path}")
        return []
    
    data = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

def mock_triage_model(symptoms: str) -> str:
    """
    Mock function representing the LLM triage call. 
    In a real implementation, this would call the MedAgent API or LLM directly.
    """
    symptoms = symptoms.lower()
    if "worst headache" in symptoms or "crushing chest pain" in symptoms:
        return "Emergency"
    elif "bleeding" in symptoms and "stopped" not in symptoms.replace("has not stopped", "continuing"):
        return "Urgent" # simplistic logic for the mock
    else:
        return "Routine"

def run_evaluation():
    logger.info("Starting Evaluation Suite...")
    gold_data = load_gold_set(GOLD_SET_PATH)
    
    if not gold_data:
        logger.warning("No data to evaluate. Exiting.")
        return

    correct = 0
    total = len(gold_data)
    
    for case in gold_data:
        predicted = mock_triage_model(case["symptoms"])
        expected = case["expected_triage"]
        
        if predicted == expected:
            correct += 1
        else:
            logger.warning(f"Mismatch in {case['case_id']}: Expected {expected}, got {predicted}")
            
    accuracy = (correct / total) * 100
    
    logger.info(f"--- Evaluation Results ---")
    logger.info(f"Total Cases: {total}")
    logger.info(f"Correct: {correct}")
    logger.info(f"Triage Accuracy: {accuracy:.2f}%")
    
    if accuracy < 80.0:
        logger.error("Accuracy is below the 80% threshold for production safety.")
    else:
        logger.info("Accuracy meets the production safety threshold.")

if __name__ == "__main__":
    run_evaluation()
