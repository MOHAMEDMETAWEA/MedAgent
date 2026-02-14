from .state import AgentState
from config import settings, get_prompt_path
from utils.safety import add_safety_disclaimer
from agents.persistence_agent import PersistenceAgent
import re
import logging
import json

logger = logging.getLogger(__name__)

class ReportAgent:
    """
    Generative Report Agent – RAG-grounded report generation.
    Produces: medical report, doctor summary, patient instructions (simple language).
    Also handles Persistence and Versioning.
    """
    def __init__(self, model=None):
        model = model or settings.OPENAI_MODEL
        self.llm = ChatOpenAI(
            model=model,
            temperature=settings.LLM_TEMPERATURE_DOCTOR,
            api_key=settings.OPENAI_API_KEY,
        )
        self.retriever = MedicalRetriever()
        self.persistence = PersistenceAgent()

    def _load_prompt(self, filename: str) -> str:
        try:
            path = get_prompt_path(filename)
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error("Error loading prompt %s: %s", filename, e)
            return ""

    def _parse_sections(self, text: str) -> tuple:
        """Extract MEDICAL_REPORT, DOCTOR_SUMMARY, PATIENT_INSTRUCTIONS from agent output."""
        medical = ""
        doctor_summary = ""
        patient_instructions = ""
        if not text:
            return medical, doctor_summary, patient_instructions
        flags = re.DOTALL | re.IGNORECASE
        m1 = re.search(r"MEDICAL_REPORT\s*[:\-]\s*(.*?)(?=DOCTOR_SUMMARY|PATIENT_INSTRUCTIONS|$)", text, flags)
        m2 = re.search(r"DOCTOR_SUMMARY\s*[:\-]\s*(.*?)(?=PATIENT_INSTRUCTIONS|MEDICAL_REPORT|$)", text, flags)
        m3 = re.search(r"PATIENT_INSTRUCTIONS\s*[:\-]\s*(.*?)(?=MEDICAL_REPORT|DOCTOR_SUMMARY|$)", text, flags)
        if m1:
            medical = m1.group(1).strip()
        if m2:
            doctor_summary = m2.group(1).strip()
        if m3:
            patient_instructions = m3.group(1).strip()
        if not medical and not doctor_summary and not patient_instructions:
            medical = text[:3000].strip()
        return medical, doctor_summary, patient_instructions

    def process(self, state: AgentState):
        print("--- REPORT AGENT: GENERATIVE REPORT & PERSISTENCE ---")
        patient_summary = state.get("patient_info", {}).get("summary", "")
        preliminary_diagnosis = state.get("preliminary_diagnosis", "")
        doctor_notes = state.get("doctor_notes", "")
        appointment_details = state.get("appointment_details", "")
        lang = state.get("language", "en")
        
        session_id = state.get("session_id", "audit-session")
        patient_id = state.get("user_id", "GUEST")
        
        if not patient_summary and not preliminary_diagnosis:
            return {
                "report_medical": "",
                "report_doctor_summary": "",
                "report_patient_instructions": "",
                "next_step": "end",
            }
        
        # RAG Retrieval
        query = f"{patient_summary} {preliminary_diagnosis}".strip()
        knowledge = self.retriever.retrieve(query) if query else "No guidelines retrieved."
        
        template = self._load_prompt("report_agent.txt")
        if not template:
            # Fallback
            template = """
            Generate a medical report based on:
            Knowledge: {knowledge}
            Summary: {patient_summary}
            Diagnosis: {preliminary_diagnosis}
            Notes: {doctor_notes}
            Appointment: {appointment_details}
            
            Format: MEDICAL_REPORT: ..., DOCTOR_SUMMARY: ..., PATIENT_INSTRUCTIONS: ...
            """
            
        prompt = template.format(
            knowledge=knowledge,
            patient_summary=patient_summary,
            preliminary_diagnosis=preliminary_diagnosis,
            doctor_notes=doctor_notes,
            appointment_details=appointment_details,
        )
        
        # Bilingual instruction
        lang_instruction = "Respond in ENGLISH." if lang == "en" else "Respond in ARABIC (اللغة العربية). Ensure headers are still MEDICAL_REPORT, etc. just translated content."
        
        try:
            response = self.llm.invoke([
                SystemMessage(content=f"You are a Generative Report Agent. {lang_instruction} Output only the three sections with exact ENGLISH headers: MEDICAL_REPORT, DOCTOR_SUMMARY, PATIENT_INSTRUCTIONS."),
                HumanMessage(content=prompt),
            ])
            content = response.content or ""
            medical, doctor_summary, patient_instructions = self._parse_sections(content)
            
            # Add disclaimer
            disclaimer_txt = "No specific instructions." if lang == "en" else "لا توجد تعليمات محددة."
            patient_instructions = add_safety_disclaimer(patient_instructions) if patient_instructions else add_safety_disclaimer(disclaimer_txt)
            
            # Unified response for Frontend
            final_response = f"**Medical Report**:\n{medical}\n\n**Summary**:\n{doctor_summary}\n\n**Instructions**:\n{patient_instructions}"
            
            # --- PERSISTENCE: Save Report ---
            report_status = "flagged" if state.get("critical_alert") else "approved"
            full_report_json = json.dumps({
                "medical_report": medical,
                "doctor_summary": doctor_summary,
                "patient_instructions": patient_instructions,
                "full_text": final_response
            })
            
            self.persistence.save_medical_report(
                session_id=session_id,
                patient_id=patient_id,
                content_json=full_report_json,
                report_type="comprehensive",
                lang=lang,
                status=report_status
            )
            
            return {
                "report_medical": medical,
                "report_doctor_summary": doctor_summary,
                "report_patient_instructions": patient_instructions,
                "final_response": final_response, # Update final response for UI
                "next_step": "end"
            }
        except Exception as e:
            logger.exception("Report agent error: %s", e)
            return {
                "final_response": f"Report generation failed: {e}",
                "report_medical": "",
                "next_step": "end",
            }
