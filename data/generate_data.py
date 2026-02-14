import json
import sys
from pathlib import Path
import random
import pandas as pd
from faker import Faker

# Run from project root so config and paths resolve
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from config import settings

fake = Faker()

def generate_professional_data():
    """
    Generates a high-quality, structured medical knowledge base for RAG.
    """
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. High-Resolution Medical Protocols (Expanded)
    guidelines = [
        {
            "category": "Cardiology",
            "condition": "Acute Myocardial Infarction (Heart Attack)",
            "guideline": "Immediate diagnosis via ECG and Troponin levels. Time-to-reperfusion is critical.",
            "indicators": "Substernal chest pain, radiating to left arm/jaw, diaphoresis (sweating), nausea, dyspnea.",
            "treatment": "Aspirin 325mg (chewed), Nitroglycerin (if SBP >90), immediate transport to PCI center."
        },
        {
            "category": "Endocrinology",
            "condition": "Diabetic Ketoacidosis (DKA)",
            "guideline": "Emergency life-threatening condition in type 1/2 diabetes.",
            "indicators": "Fruity breath odor (acetone), Kussmaul respirations, polyuria, polydipsia, confusion.",
            "treatment": "IV fluid resuscitation (Normal Saline), Insulin infusion 0.1U/kg/hr, Potassium replacement."
        },
        {
            "category": "Respiratory",
            "condition": "Pneumonia",
            "guideline": "Infection of lung parenchyma. Differentiate between CAP and HAP via history.",
            "indicators": "Productive cough (rusty or green sputum), pleuritic chest pain, fever, rales/crackles on auscultation.",
            "treatment": "Empiric antibiotics (e.g., Azithromycin + Ceftriaxone for CAP). CURB-65 score for admission."
        },
        {
            "category": "Neurology",
            "condition": "Ischemic Stroke",
            "guideline": "Time is Brain. Window for thrombolysis (tPA) is 4.5 hours from Last Known Well.",
            "indicators": "Facial drooping, arm weakness, speech difficulty (FAST), visual field defects.",
            "treatment": "CT scan without contrast to rule out hemorrhage. Stabilize BP. Thrombectomy evaluation."
        },
        {
            "category": "Gastroenterology",
            "condition": "Acute Appendicitis",
            "guideline": "Most common surgical emergency. High risk of perforation if delayed >24h.",
            "indicators": "Periumbilical pain migrating to Right Lower Quadrant (McBurney's point), guarding, rebound tenderness.",
            "treatment": "NPO (Nothing by mouth), IV antibiotics, surgical appendectomy."
        },
        {
            "category": "Respiratory",
            "condition": "Asthma Exacerbation",
            "guideline": "Reversible airway obstruction. Monitor SpO2 and Peak Flow.",
            "indicators": "Wheezing, accessory muscle use, 'silent chest' is an ominous sign.",
            "treatment": "SABA (Albuterol) nebulizer, systemic corticosteroids (Prednisone), Oxygen."
        },
        {
            "category": "Infectious Disease",
            "condition": "Sepsis",
            "guideline": "Dysregulated host response to infection. High mortality rate.",
            "indicators": "qSOFA score >= 2 (Altered mental status, SBP <=100, RR >=22). Hypothermia or fever.",
            "treatment": "Sepsis 3-hour bundle: Lactate level, Blood cultures, Broad-spectrum antibiotics, Fluid bolus."
        }
    ]
    
    with open(settings.MEDICAL_GUIDELINES_PATH, 'w', encoding='utf-8') as f:
        json.dump(guidelines, f, indent=4)
    print(f"Generated {settings.MEDICAL_GUIDELINES_PATH}")

    # 2. Synthetic Patient History for long-term memory testing
    patients = []
    conditions = ["Hypertension", "Type 2 Diabetes", "Asthma", "CKD Stage 2", "None"]
    for _ in range(100):
        patients.append({
            "patient_id": fake.uuid4(),
            "name": fake.name(),
            "age": random.randint(18, 85),
            "gender": random.choice(["Male", "Female"]),
            "chronic_conditions": random.sample(conditions, random.randint(1, 2)),
            "last_bp": f"{random.randint(110, 160)}/{random.randint(70, 100)}",
            "last_hba1c": round(random.uniform(5.5, 9.0), 1)
        })
    pd.DataFrame(patients).to_csv(settings.DATA_DIR / 'patient_registry.csv', index=False)
    print(f"Generated {settings.DATA_DIR / 'patient_registry.csv'}")

if __name__ == "__main__":
    generate_professional_data()
