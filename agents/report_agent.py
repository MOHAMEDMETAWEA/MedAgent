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
import os
import textwrap

logger = logging.getLogger(__name__)

class ReportAgent:
    """
    Generative Report Agent – RAG-grounded report generation.
    Produces: medical report, doctor summary, patient instructions (simple language).
    Also handles Persistence and Versioning.
    """
    def __init__(self, model=None):
        self.default_model = model or settings.OPENAI_MODEL
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
        
        # Bilingual instruction
        lang_instruction = "Respond in ENGLISH." if lang == "en" else "Respond in ARABIC (اللغة العربية). Ensure headers are still MEDICAL_REPORT, etc. just translated content."
        
        mode_instruction = ""
        if mode == "patient":
            mode_instruction = "IMPORTANT: For PATIENT mode, ensure PATIENT_INSTRUCTIONS are exceptionally clear and reassuring. Avoid complex jargon in the instructions section."
        else:
            mode_instruction = "IMPORTANT: For DOCTOR mode, ensure MEDICAL_REPORT and DOCTOR_SUMMARY use high-level clinical language and diagnostic codes where applicable."

        try:
            model_override = state.get("model_used") or self.default_model
            llm = ChatOpenAI(model=model_override, temperature=settings.LLM_TEMPERATURE_DOCTOR, api_key=settings.OPENAI_API_KEY)
            response = llm.invoke([
                SystemMessage(content=f"You are a Generative Report Agent. {lang_instruction} {mode_instruction} Output only the three sections with exact ENGLISH headers: MEDICAL_REPORT, DOCTOR_SUMMARY, PATIENT_INSTRUCTIONS."),
                HumanMessage(content=prompt),
            ])
        except Exception as e:
            sec = state.get("secondary_model")
            if not sec:
                logger.error(f"Report agent error: {e}")
                return {
                    "final_response": f"Report generation failed: {e}",
                    "report_medical": "",
                    "next_step": "end",
                }
            llm = ChatOpenAI(model=sec, temperature=settings.LLM_TEMPERATURE_DOCTOR, api_key=settings.OPENAI_API_KEY)
            response = llm.invoke([
                SystemMessage(content=f"You are a Generative Report Agent. {lang_instruction} {mode_instruction} Output only the three sections with exact ENGLISH headers: MEDICAL_REPORT, DOCTOR_SUMMARY, PATIENT_INSTRUCTIONS."),
                HumanMessage(content=prompt),
            ])
        try:
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

    def _draw_section_header(self, pdf, title, color):
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*color)
        pdf.cell(0, 8, title, ln=True)
        pdf.set_draw_color(*color)
        pdf.set_line_width(0.5)
        pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 40, pdf.get_y())
        pdf.ln(3)

    def generate_pdf(self, report_data: dict, output_path: str):
        """Generate a clinical PDF report using fpdf2 with premium branding."""
        try:
            from fpdf import FPDF
            
            class PDF(FPDF):
                def header(self):
                    # Background header bar
                    self.set_fill_color(46, 125, 50)
                    self.rect(0, 0, 210, 40, "F")
                    
                    self.set_y(15)
                    self.set_font("Helvetica", "B", 22)
                    self.set_text_color(255, 255, 255)
                    self.cell(0, 10, "MEDAGENT GLOBAL", ln=True, align="C")
                    self.set_font("Helvetica", "", 10)
                    self.cell(0, 5, "PRECISION CLINICAL INTELLIGENCE HUB", ln=True, align="C")
                    self.ln(20)

                def footer(self):
                    self.set_y(-20)
                    self.set_font("Helvetica", "I", 8)
                    self.set_text_color(160, 160, 160)
                    self.cell(0, 10, f"Page {self.page_no()} | MedAgent AI Workforce | Secure & Encrypted Report", align="L")
                    self.cell(0, 10, f"ID: {self.report_id_str}", align="R")

            pdf = PDF()
            pdf.report_id_str = str(report_data.get('patient_id', 'GUEST'))[:8]
            pdf.add_page()
            
            # Sub-header with Patient Details
            pdf.set_fill_color(245, 248, 245)
            pdf.set_text_color(50, 50, 50)
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 10, "  PATIENT SUMMARY", ln=True, fill=True)
            
            pdf.set_font("Helvetica", "", 10)
            pdf.ln(2)
            pdf.cell(60, 8, f"  Name: {report_data.get('patient_name', 'N/A')}", ln=False)
            pdf.cell(60, 8, f"  ID: {report_data.get('patient_id', 'N/A')}", ln=False)
            pdf.cell(60, 8, f"  Date: {report_data.get('date', 'N/A')}", ln=True)
            pdf.ln(5)

            # Main Content
            sections = [
                ("CLINICAL OBSERVATIONS", report_data.get("medical_report", ""), (46, 125, 50)),
                ("DIAGNOSTIC SUMMARY", report_data.get("doctor_summary", ""), (25, 118, 210)),
                ("TREATMENT & INSTRUCTIONS", report_data.get("patient_instructions", ""), (211, 47, 47))
            ]
            
            for title, content, color in sections:
                self._draw_section_header(pdf, title, color)
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(60, 60, 60)
                pdf.multi_cell(0, 6, content)
                pdf.ln(8)
            
            # Bottom Disclaimer
            pdf.set_y(-45)
            pdf.set_draw_color(200, 200, 200)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(2)
            pdf.set_font("Helvetica", "I", 7)
            pdf.set_text_color(150, 150, 150)
            disclaimer = "This report is generated by MedAgent's distributed agentic workforce. It uses Retrieval-Augmented Generation (RAG) to cross-reference medical literature. This document is a clinical simulation and must be validated by a board-certified physician before any medical intervention."
            pdf.multi_cell(0, 4, disclaimer, align="C")
            
            pdf.output(output_path)
            return True
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            return False

    def generate_image(self, report_data: dict, output_path: str):
        """Generate a clinical report image with a premium, modern design."""
        try:
            from PIL import Image, ImageDraw, ImageFont

            # Canvas setup (Higher resolution for premium feel)
            width, height = 1000, 1400
            image = Image.new("RGB", (width, height), (248, 250, 252)) # Sleek light gray bg
            draw = ImageDraw.Draw(image)

            # Font Loading
            font_path = "C:\\Windows\\Fonts\\arial.ttf"
            def get_font(size, bold=False):
                try:
                    return ImageFont.truetype(font_path, size)
                except:
                    return ImageFont.load_default()

            h_font = get_font(42)
            s_font = get_font(28)
            t_font = get_font(20)
            m_font = get_font(18)
            f_font = get_font(14)

            # Premium Header Card
            draw.rectangle([0, 0, width, 180], fill=(30, 64, 175)) # Deep Blue
            draw.text((width // 2, 80), "MEDAGENT CLINICAL HUB", fill=(255, 255, 255), font=h_font, anchor="mm")
            draw.text((width // 2, 130), "INTELLIGENT DIAGNOSTIC REPORT", fill=(191, 219, 254), font=m_font, anchor="mm")
            
            y = 220
            
            # Patient Data Row
            draw.rectangle([50, y, width-50, y+100], fill=(255, 255, 255), outline=(226, 232, 240), width=1)
            draw.text((70, y+35), f"Patient ID: {report_data.get('patient_id', 'GUEST')[:10]}", fill=(71, 85, 105), font=t_font)
            draw.text((width-70, y+35), f"Generated: {report_data.get('date', 'N/A')}", fill=(71, 85, 105), font=t_font, anchor="ra")
            y += 140

            sections = [
                ("System Observations", report_data.get("medical_report", ""), (30, 64, 175)),
                ("Clinical Summary", report_data.get("doctor_summary", ""), (5, 150, 105)),
                ("Recommended Actions", report_data.get("patient_instructions", ""), (185, 28, 28))
            ]

            for title, content, color in sections:
                # Section Title with Icon-like bullet
                draw.rectangle([50, y, 65, y+30], fill=color)
                draw.text((80, y), title.upper(), fill=color, font=s_font)
                y += 45
                
                # Card around content
                lines = textwrap.wrap(content, width=80)
                card_height = len(lines) * 28 + 40
                draw.rectangle([50, y, width-50, y+card_height], fill=(255, 255, 255), outline=(241, 245, 249), width=1)
                
                ty = y + 20
                for line in lines:
                    draw.text((70, ty), line, fill=(30, 41, 59), font=t_font)
                    ty += 28
                y += card_height + 40

            # Footer
            draw.rectangle([0, height-80, width, height], fill=(15, 23, 42)) # Near Black
            disclaimer = "CONFIDENTIAL | AI-GENERATED REPORT | VERIFIED BY MEDAGENT CLUSTER 7"
            draw.text((width // 2, height-40), disclaimer, fill=(148, 163, 184), font=f_font, anchor="mm")

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
