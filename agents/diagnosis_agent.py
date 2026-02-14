"""
Diagnosis Agent with Enhanced Safety and Global Usability.
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from rag.retriever import MedicalRetriever
from .state import AgentState
from config import settings, get_prompt_path
from utils.safety import detect_critical_symptoms
import logging

logger = logging.getLogger(__name__)

class DiagnosisAgent:
    """
    Advanced Diagnosis Agent with Self-Reflection and RAG Grounding.
    Enhanced with safety checks and global usability.
    """
    def __init__(self, model=None):
        model = model or settings.OPENAI_MODEL
        self.llm = ChatOpenAI(
            model=model, 
            temperature=settings.LLM_TEMPERATURE_DIAGNOSIS,
            api_key=settings.OPENAI_API_KEY
        )
        self.retriever = MedicalRetriever()

    def _load_prompt(self, filename: str) -> str:
        """Load prompt file using configurable path."""
        try:
            prompt_path = get_prompt_path(filename)
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"Prompt file not found: {filename}")
            return ""
        except Exception as e:
            logger.error(f"Error loading prompt {filename}: {e}")
            return ""

    def process(self, state: AgentState):
        print("--- DIAGNOSIS AGENT: HIGH-ACCURACY ANALYSIS ---")
        patient_summary = state['patient_info'].get('summary', '')
        
        if not patient_summary:
            return {
                "preliminary_diagnosis": "Insufficient patient information for diagnosis.",
                "critical_alert": False,
                "next_step": "scheduling"
            }
        
        try:
            # 1. Evidence Retrieval
            knowledge = self.retriever.retrieve(patient_summary)
            
            # 2. Initial Differential Diagnosis
            initial_template = self._load_prompt('diagnosis_agent.txt')
            if not initial_template:
                return {
                    "preliminary_diagnosis": "System configuration error. Please contact support.",
                    "critical_alert": False,
                    "next_step": "scheduling"
                }
            
            initial_prompt = initial_template.format(
                knowledge=knowledge, 
                patient_summary=patient_summary
            )
            
            initial_diagnosis = self.llm.invoke([SystemMessage(content=initial_prompt)])
            
            # 3. SELF-REFLECTION / CRITIQUE
            reflection_template = self._load_prompt('audit_reflection.txt')
            if reflection_template:
                reflection_prompt = reflection_template.format(
                    knowledge=knowledge, 
                    initial_diagnosis=initial_diagnosis.content
                )
                
                final_diagnosis = self.llm.invoke([
                    SystemMessage(content="You are a Clinical Auditor. Your job is to ensure AI diagnoses are grounded in medical evidence and express appropriate uncertainty."),
                    HumanMessage(content=reflection_prompt)
                ])
            else:
                final_diagnosis = initial_diagnosis
            
            # Enhanced critical alert detection
            diagnosis_text = final_diagnosis.content.lower()
            critical_keywords = ["emergency", "critical", "immediate", "red flag", 
                               "infarction", "stroke", "sepsis", "cardiac arrest",
                               "life-threatening", "urgent medical attention"]
            critical = any(keyword in diagnosis_text for keyword in critical_keywords)
            
            # Also check patient summary for critical symptoms
            is_critical_from_summary, _ = detect_critical_symptoms(patient_summary)
            critical = critical or is_critical_from_summary
            
            # Do not add disclaimer here; doctor agent adds it to final output

            return {
                "preliminary_diagnosis": final_diagnosis.content,
                "critical_alert": critical,
                "next_step": "scheduling"
            }
        except Exception as e:
            logger.error(f"Error in diagnosis agent: {e}")
            return {
                "preliminary_diagnosis": f"An error occurred during diagnosis. Please consult a healthcare professional. Error: {str(e)}",
                "critical_alert": True,  # Err on the side of caution
                "next_step": "scheduling"
            }
