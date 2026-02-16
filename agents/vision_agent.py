"""
Vision Analysis Agent - Processes and analyzes medical images.
"""
import os
import base64
import logging
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from .state import AgentState
from config import settings

logger = logging.getLogger(__name__)

class VisionAnalysisAgent:
    """
    Analyzes user-uploaded medical images (rashes, reports, etc.) using GPT-4o Vision.
    """
    def __init__(self, model=None):
        # Default to GPT-4o for Multimodal capabilities
        self.model_name = model or "gpt-4o" 
        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=0.0,
            api_key=settings.OPENAI_API_KEY
        )

    def _encode_image(self, image_path: str):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def process(self, state: AgentState) -> Dict[str, Any]:
        """Process an image and return structured findings."""
        image_path = state.get("image_path")
        if not image_path or not os.path.exists(image_path):
            return {"visual_findings": {"status": "skipped", "reason": "No image provided"}}

        print(f"--- VISION ANALYSIS AGENT: ANALYZING {os.path.basename(image_path)} ---")
        
        try:
            base64_image = self._encode_image(image_path)
            
            system_prompt = (
                "You are the MEDAgent Vision Analysis Specialist. "
                "Your task is to analyze the provided medical image (e.g., skin condition, report, injury) "
                "and describe visual findings in a structured format. "
                "BE CAREFUL and OBJECTIVE. Do NOT provide a definitive medical diagnosis. "
                "Identify visible features, anomalies, and severity markers. "
                "Format your response as a JSON object with: visual_findings, possible_conditions (list), "
                "confidence (0-1.0), severity_level (low/moderate/high), and requires_human_review (boolean)."
            )

            # Detect language
            lang = state.get("language", "en")
            if lang == "ar":
                system_prompt += " Provide descriptions in Arabic when appropriate for the 'visual_findings' section."

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(
                    content=[
                        {"type": "text", "text": "Please analyze this medical image for visual features."},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                        },
                    ]
                )
            ]

            response = self.llm.invoke(messages)
            content = response.content
            
            # Simple manual JSON parsing (assuming direct LLM output or wrapping)
            # In production, use JsonOutputParser
            import json
            try:
                # Clean code blocks if present
                clean_content = content.replace("```json", "").replace("```", "").strip()
                findings = json.loads(clean_content)
            except:
                findings = {
                    "visual_findings": content,
                    "possible_conditions": [],
                    "confidence": 0.5,
                    "severity_level": "moderate",
                    "requires_human_review": True
                }

            # Update flags
            needs_review = findings.get("requires_human_review", False) or findings.get("severity_level") == "high"
            
            return {
                "visual_findings": findings,
                "requires_human_review": state.get("requires_human_review", False) or needs_review,
                "status": "Vision Analysis Complete / تم الانتهاء من تحليل الصور"
            }

        except Exception as e:
            logger.error(f"Vision Analysis failed: {e}")
            return {
                "visual_findings": {"error": str(e), "status": "failed"},
                "requires_human_review": True
            }
