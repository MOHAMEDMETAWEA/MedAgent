"""
Response Agent (formerly Report Agent) - Formats the final user output.
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from .state import AgentState
from config import settings, get_prompt_path
from utils.safety import add_safety_disclaimer
import logging

logger = logging.getLogger(__name__)

class ResponseAgent:
    """
    Formats the final response into clear, safe, user-friendly text.
    Handles localization (English/Arabic).
    """
    def __init__(self, model=None):
        self.llm = ChatOpenAI(
            model=model or settings.OPENAI_MODEL,
            temperature=settings.LLM_TEMPERATURE_DOCTOR,
            api_key=settings.OPENAI_API_KEY
        )

    def _load_prompt(self, filename):
        return get_prompt_path(filename).read_text(encoding='utf-8')

    def process(self, state: AgentState):
        print("--- RESPONSE AGENT: FORMATTING OUTPUT ---")
        diagnosis = state.get('preliminary_diagnosis', '')
        patient_info = state.get('patient_info', {})
        urgency = patient_info.get('urgency', 'UNKNOWN')
        lang = state.get('language', 'en')
        
        # If safety blocked it
        if diagnosis.startswith("Output blocked") or "withheld" in diagnosis:
            msg = diagnosis
            if lang == "ar":
                msg = "تم حجب الإجابة لسلامتك الطبية. يرجى استشارة طبيب."
            return {
                "final_response": add_safety_disclaimer(msg),
                "next_step": "end"
            }

        prompt_template = self._load_prompt('report_agent.txt') 
        
        # Add language instruction
        lang_instruction = "Respond in ENGLISH." if lang == "en" else "Respond in ARABIC (اللغة العربية)."
        
        prompt = prompt_template.format(
            knowledge=state.get('retrieved_docs', ''),
            patient_summary=patient_info.get('summary', ''),
            preliminary_diagnosis=diagnosis,
            doctor_notes=state.get('doctor_notes', 'N/A'),
            appointment_details=str(urgency)
        )
        
        full_prompt = f"{lang_instruction}\n\n{prompt}"

        try:
            response = self.llm.invoke([
                SystemMessage(content=f"You are a Response Agent. {lang_instruction} Format clarity."),
                HumanMessage(content=full_prompt)
            ])
            
            final_content = response.content
            final_content = add_safety_disclaimer(final_content)
            
            return {
                "final_response": final_content,
                "report_medical": final_content, 
                "next_step": "calendar"
            }
        except Exception as e:
            logger.error(f"Response error: {e}")
            return {
                "final_response": "Error generating response." if lang=="en" else "حدث خطأ في النظام.",
                "next_step": "end"
            }
