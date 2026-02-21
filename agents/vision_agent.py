"""
Vision Analysis Agent - Clinical-Grade Medical Image Analysis.
Uses GPT-4o Vision with structured prompt for safety and accuracy.
"""
import os
import base64
import logging
import json
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from .state import AgentState
from config import settings, get_prompt_path

logger = logging.getLogger(__name__)

# Supported image MIME types
MIME_MAP = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
    "heic": "image/heic",
    "dicom": "application/dicom",
}

class VisionAnalysisAgent:
    """
    Analyzes user-uploaded medical images (X-ray, CT, MRI, skin, lab reports)
    using GPT-4o Vision with clinical-grade structured prompts.
    """
    def __init__(self, model=None):
        self.model_name = model or "gpt-4o"
        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=0.0,
            api_key=settings.OPENAI_API_KEY
        )

    def _load_prompt(self, filename: str) -> str:
        try:
            return get_prompt_path(filename).read_text(encoding='utf-8')
        except Exception as e:
            logger.error(f"Error loading prompt {filename}: {e}")
            return ""

    def _encode_image(self, image_path: str) -> str:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def _get_mime_type(self, image_path: str) -> str:
        ext = os.path.splitext(image_path)[1].lower().strip(".")
        return MIME_MAP.get(ext, "image/jpeg")

    def process(self, state: AgentState) -> Dict[str, Any]:
        """Process a medical image and return structured clinical findings."""
        image_path = state.get("image_path")
        if not image_path or not os.path.exists(image_path):
            return {"visual_findings": {"status": "skipped", "reason": "No image provided"}}

        print(f"--- VISION ANALYSIS AGENT: ANALYZING {os.path.basename(image_path)} ---")

        try:
            base64_image = self._encode_image(image_path)
            mime_type = self._get_mime_type(image_path)

            # Load structured prompt template
            template = self._load_prompt("vision_agent.txt")

            # Inject patient demographics if available
            age = state.get("user_age", "Unknown")
            gender = state.get("user_gender", "Unknown")
            country = state.get("user_country", "Unknown")

            if template:
                system_prompt = template.replace("{age}", str(age)).replace("{gender}", str(gender)).replace("{country}", str(country))
            else:
                # Fallback inline prompt
                system_prompt = (
                    "You are the MEDAgent Vision Analysis Specialist. "
                    "Analyze the provided medical image and describe visual findings in structured JSON format. "
                    "BE CAREFUL and OBJECTIVE. Do NOT provide a definitive medical diagnosis. "
                    "Include: visual_findings, possible_conditions (list), differential_diagnosis (list), "
                    "confidence (0-1.0), severity_level (low/moderate/high/critical), "
                    "recommended_actions (list), requires_human_review (boolean), uncertainty_notes."
                )

            # Detect language
            lang = state.get("language", "en")
            if lang == "ar":
                system_prompt += "\nProvide descriptions in Arabic when appropriate for the 'visual_findings' section."

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(
                    content=[
                        {"type": "text", "text": "Analyze this medical image. Provide a structured clinical assessment."},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{base64_image}"},
                        },
                    ]
                )
            ]

            response = self.llm.invoke(messages)
            content = response.content

            # Parse structured JSON output
            try:
                clean_content = content.replace("```json", "").replace("```", "").strip()
                findings = json.loads(clean_content)
            except (json.JSONDecodeError, ValueError):
                findings = {
                    "image_type": "Unknown",
                    "visual_findings": content,
                    "possible_conditions": [],
                    "differential_diagnosis": [],
                    "confidence": 0.5,
                    "severity_level": "moderate",
                    "recommended_actions": ["Consult a healthcare professional"],
                    "requires_human_review": True,
                    "uncertainty_notes": "Could not parse structured output from vision model"
                }

            # Enforce confidence threshold safety rule
            confidence = findings.get("confidence", 0.5)
            severity = findings.get("severity_level", "moderate")

            if confidence < 0.7:
                findings["requires_human_review"] = True
                if not findings.get("uncertainty_notes"):
                    findings["uncertainty_notes"] = "Confidence below threshold (0.7) — professional review recommended."

            if severity in ("high", "critical"):
                findings["requires_human_review"] = True

            # Always add medical disclaimer
            findings["disclaimer"] = (
                "This analysis is AI-generated and NOT a definitive medical diagnosis. "
                "Always consult a qualified healthcare professional for clinical decisions."
            )

            needs_review = findings.get("requires_human_review", False)

            return {
                "visual_findings": findings,
                "requires_human_review": state.get("requires_human_review", False) or needs_review,
                "status": "Vision Analysis Complete / تم الانتهاء من تحليل الصور"
            }

        except Exception as e:
            logger.error(f"Vision Analysis failed: {e}")
            return {
                "visual_findings": {
                    "error": str(e),
                    "status": "failed",
                    "requires_human_review": True,
                    "disclaimer": "Image analysis failed. Please consult a healthcare professional."
                },
                "requires_human_review": True
            }

