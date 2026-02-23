from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from rag.retriever import MedicalRetriever
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
        logger.info("--- REPORT AGENT: GENERATIVE REPORT & EXPORT ---")
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
        
        visual_findings = state.get("visual_findings", {})
        visual_text = ""
        if visual_findings and visual_findings.get("status") != "skipped":
            visual_text = f"Visual Analysis: {visual_findings.get('visual_findings')}\nConfidence: {visual_findings.get('confidence')}\nSeverity: {visual_findings.get('severity_level')}"

        template = self._load_prompt("report_agent.txt")
        if not template:
            # Fallback
            template = """
            Generate a medical report based on:
            Knowledge: {knowledge}
            Summary: {patient_summary}
            Visual Data: {visual_text}
            Diagnosis: {preliminary_diagnosis}
            Notes: {doctor_notes}
            Appointment: {appointment_details}
            
            Format: MEDICAL_REPORT: ..., DOCTOR_SUMMARY: ..., PATIENT_INSTRUCTIONS: ...
            """
            
        prompt = template.format(
            knowledge=knowledge,
            patient_summary=patient_summary,
            visual_text=visual_text,
            preliminary_diagnosis=preliminary_diagnosis,
            doctor_notes=doctor_notes,
            appointment_details=appointment_details,
        )
        
        # Metadata for adaptation
        mode = state.get("interaction_mode", "patient")
        role = state.get("user_role", "patient")
        
        # Bilingual instruction
        lang_instruction = "Respond in ENGLISH." if lang == "en" else "Respond in ARABIC (اللغة العربية). Ensure headers are still MEDICAL_REPORT, etc. just translated content."
        
        mode_instruction = ""
        if mode == "patient":
            mode_instruction = "IMPORTANT: For PATIENT mode, ensure PATIENT_INSTRUCTIONS are exceptionally clear and reassuring. Avoid complex jargon in the instructions section."
        else:
            mode_instruction = "IMPORTANT: For DOCTOR mode, ensure MEDICAL_REPORT and DOCTOR_SUMMARY use high-level clinical language and diagnostic codes where applicable."

        try:
            response = self.llm.invoke([
                SystemMessage(content=f"You are a Generative Report Agent. {lang_instruction} {mode_instruction} Output only the three sections with exact ENGLISH headers: MEDICAL_REPORT, DOCTOR_SUMMARY, PATIENT_INSTRUCTIONS."),
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
            
            report_id = self.persistence.save_medical_report(
                session_id=session_id,
                patient_id=patient_id,
                content_json=full_report_json,
                report_type="comprehensive",
                lang=lang,
                status=report_status
            )
            
            return {
                "report_id": report_id,
                "report_medical": medical,
                "report_doctor_summary": doctor_summary,
                "report_patient_instructions": patient_instructions,
                "final_response": final_response, # Update final response for UI
                "next_step": "end"
            }
        except Exception as e:
            logger.error(f"Report agent error: {e}")
            return {
                "final_response": f"Report generation failed: {e}",
                "report_medical": "",
                "next_step": "end",
            }

    def generate_pdf(self, report_data: dict, output_path: str):
        """Generate a clinical PDF report using fpdf2 with enhanced styling."""
        try:
            from fpdf import FPDF
            
            # Use a subclass to add header/footer
            class PDF(FPDF):
                def header(self):
                    self.set_font("Helvetica", "B", 15)
                    self.set_text_color(46, 125, 50) # Green
                    self.cell(0, 10, "MEDAGENT GLOBAL MEDICAL HUB", ln=True, align="C")
                    self.set_draw_color(46, 125, 50)
                    self.line(10, 22, 200, 22)
                    self.ln(10)

                def footer(self):
                    self.set_y(-15)
                    self.set_font("Helvetica", "I", 8)
                    self.set_text_color(128, 128, 128)
                    self.cell(0, 10, f"Page {self.page_no()} | Generated by MedAgent AI Workforce | Confidential", align="C")

            pdf = PDF()
            pdf.add_page()
            
            # Patient Info Box
            pdf.set_fill_color(240, 240, 240)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 8, f"Patient Report - ID: {report_data.get('patient_id', 'N/A')}", ln=True, fill=True)
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(95, 8, f"Date: {report_data.get('date', 'N/A')}", ln=False)
            pdf.cell(95, 8, f"Language: {report_data.get('lang', 'en').upper()}", ln=True)
            pdf.ln(5)

            # Body sections
            sections = {
                "MEDICAL REPORT": report_data.get("medical_report", ""),
                "DOCTOR SUMMARY": report_data.get("doctor_summary", ""),
                "PATIENT INSTRUCTIONS": report_data.get("patient_instructions", "")
            }
            
            for title, content in sections.items():
                pdf.set_font("Helvetica", "B", 12)
                pdf.set_text_color(0, 0, 0)
                pdf.cell(0, 10, title, ln=True)
                pdf.set_font("Helvetica", "", 10)
                pdf.multi_cell(0, 5, content)
                pdf.ln(4)
            
            pdf.ln(10)
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(150, 0, 0)
            pdf.multi_cell(0, 5, "DISCLAIMER: This report is generated by an AI assistant for simulation purposes only. It is grounded in medical literature via RAG but must be reviewed by a human professional prior to clinical action.")
            
            pdf.output(output_path)
            return True
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            return False

    def generate_image(self, report_data: dict, output_path: str):
        """Generate a clinical report image using Pillow with premium look."""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import textwrap

            # Canvas setup
            width, height = 800, 1200
            background_color = (255, 255, 255)
            image = Image.new("RGB", (width, height), background_color)
            draw = ImageDraw.Draw(image)

            # Font Loading
            font_path = "C:\\Windows\\Fonts\\arial.ttf"
            def get_font(size, bold=False):
                try:
                    return ImageFont.truetype(font_path, size)
                except:
                    return ImageFont.load_default()

            h_font = get_font(28)
            s_font = get_font(22)
            t_font = get_font(16)
            f_font = get_font(12)

            y = 40
            
            # Header Bar
            draw.rectangle([0, 0, width, 100], fill=(46, 125, 50))
            draw.text((width // 2, 50), "MEDAGENT CLINICAL REPORT", fill=(255, 255, 255), font=h_font, anchor="mm")
            y = 130

            # Metadata
            draw.text((40, y), f"Patient ID: {report_data.get('patient_id', 'N/A')}", fill=(100, 100, 100), font=t_font)
            draw.text((width - 40, y), f"Date: {report_data.get('date', 'N/A')}", fill=(100, 100, 100), font=t_font, anchor="ra")
            y += 40
            draw.line([40, y, width-40, y], fill=(200, 200, 200), width=1)
            y += 30

            sections = {
                "MEDICAL REPORT": report_data.get("medical_report", ""),
                "DOCTOR SUMMARY": report_data.get("doctor_summary", ""),
                "PATIENT INSTRUCTIONS": report_data.get("patient_instructions", "")
            }

            for title, content in sections.items():
                draw.text((40, y), title, fill=(46, 125, 50), font=s_font)
                y += 35
                lines = textwrap.wrap(content, width=85)
                for line in lines:
                    draw.text((45, y), line, fill=(0, 0, 0), font=t_font)
                    y += 22
                y += 25

            # Footer Disclaimer
            disclaimer = "DISCLAIMER: AI-generated simulation. Consult a doctor. This report is protected by AES-256 encryption in our central hub."
            draw.rectangle([0, height-60, width, height], fill=(245, 245, 245))
            draw.text((width // 2, height-30), disclaimer, fill=(100, 100, 100), font=f_font, anchor="mm")

            image.save(output_path)
            return True
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            return False

    def generate_text(self, report_data: dict, output_path: str):
        """Generate a professionally formatted plain text clinical report."""
        try:
            content = f"""
==========================================================
             MEDAGENT CLINICAL REPORT
==========================================================
Patient ID: {report_data.get('patient_id', 'N/A')}
Date      : {report_data.get('date', 'N/A')}
Language  : {report_data.get('lang', 'en').upper()}
Format    : AI-GENERATED COMPREHENSIVE
----------------------------------------------------------

1. MEDICAL REPORT
-----------------
{report_data.get('medical_report', '')}

2. DOCTOR SUMMARY
-----------------
{report_data.get('doctor_summary', '')}

3. PATIENT INSTRUCTIONS
-----------------------
{report_data.get('patient_instructions', '')}

==========================================================
DISCLAIMER: This report is generated by an AI assistant for 
simulation purposes only. It is grounded in medical 
retrieval evidence but should not be taken as final 
medical advice. Consult a qualified professional.
==========================================================
Generated by MedAgent v5.0
"""
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            return False

    def get_user_reports(self, user_id: str):
        """Retrieve all reports for a user."""
        return self.persistence.get_reports_by_patient(user_id)
