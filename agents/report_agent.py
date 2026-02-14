"""
Generative Report Agent – RAG-grounded report generation.
Produces: medical report (تقرير طبي), doctor summary (Summary للطبيب), patient instructions in simple language (تعليمات للمريض بلغة بسيطة).
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from rag.retriever import MedicalRetriever
from .state import AgentState
from config import settings, get_prompt_path
from utils.safety import add_safety_disclaimer
import re
import logging

logger = logging.getLogger(__name__)


class ReportAgent:
    """
    Generative Report Agent. Uses RAG to ground all outputs in medical guidelines.
    Outputs: medical report, doctor summary, patient instructions (simple language).
    """
    def __init__(self, model=None):
        model = model or settings.OPENAI_MODEL
        self.llm = ChatOpenAI(
            model=model,
            temperature=settings.LLM_TEMPERATURE_DOCTOR,
            api_key=settings.OPENAI_API_KEY,
        )
        self.retriever = MedicalRetriever()

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
        print("--- REPORT AGENT: GENERATIVE REPORT (RAG) ---")
        patient_summary = state.get("patient_info", {}).get("summary", "")
        preliminary_diagnosis = state.get("preliminary_diagnosis", "")
        doctor_notes = state.get("doctor_notes", "")
        appointment_details = state.get("appointment_details", "")
        if not patient_summary and not preliminary_diagnosis:
            return {
                "report_medical": "",
                "report_doctor_summary": "",
                "report_patient_instructions": "",
                "next_step": "end",
            }
        query = f"{patient_summary} {preliminary_diagnosis}".strip()
        knowledge = self.retriever.retrieve(query) if query else "No guidelines retrieved."
        template = self._load_prompt("report_agent.txt")
        if not template:
            return {
                "report_medical": "Report configuration error.",
                "report_doctor_summary": "",
                "report_patient_instructions": "",
                "next_step": "end",
            }
        prompt = template.format(
            knowledge=knowledge,
            patient_summary=patient_summary,
            preliminary_diagnosis=preliminary_diagnosis,
            doctor_notes=doctor_notes,
            appointment_details=appointment_details,
        )
        try:
            response = self.llm.invoke([
                SystemMessage(content="You are a Generative Report Agent. Output only the three sections with exact headers MEDICAL_REPORT:, DOCTOR_SUMMARY:, PATIENT_INSTRUCTIONS:. Use only the provided RAG guidelines."),
                HumanMessage(content=prompt),
            ])
            content = response.content or ""
            medical, doctor_summary, patient_instructions = self._parse_sections(content)
            patient_instructions = add_safety_disclaimer(patient_instructions) if patient_instructions else add_safety_disclaimer("No specific instructions generated. Please follow your doctor's advice.")
            return {
                "report_medical": medical,
                "report_doctor_summary": doctor_summary,
                "report_patient_instructions": patient_instructions,
                "next_step": "end",
            }
        except Exception as e:
            logger.exception("Report agent error: %s", e)
            return {
                "report_medical": "",
                "report_doctor_summary": "",
                "report_patient_instructions": add_safety_disclaimer(f"Report generation failed. Please consult a healthcare professional. ({e})"),
                "next_step": "end",
            }
