"""
FHIR & HL7 Interoperability Builder.
Converts clinical results into standardized medical data exchange formats.
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from agents.prompts.registry import PROMPT_REGISTRY
from config import settings

logger = logging.getLogger(__name__)

class InteropBuilder:
    """
    Builder responsible for generating hospital-grade interoperability messages.
    Ensures compliance with FHIR R4 and HL7 v2.x standards.
    """
    def __init__(self, model=None):
        self.llm = ChatOpenAI(
            model=model or settings.OPENAI_MODEL,
            temperature=0.0,
            api_key=settings.OPENAI_API_KEY
        )

    def build_fhir_bundle(self, clinical_data: Dict[str, Any]):
        """
        Generates a FHIR R4 Patient/Observation/Condition bundle.
        """
        logger.info("--- INTEROP: GENERATING FHIR BUNDLE ---")
        
        prompt_entry = PROMPT_REGISTRY.get("MED-INT-FHIR-001")
        if not prompt_entry:
            return {"error": "FHIR prompt not found."}

        prompt = prompt_entry.content.format(
            clinical_data=json.dumps(clinical_data, indent=2)
        )

        try:
            response = self.llm.invoke([
                SystemMessage(content="You are a Health Informatics Specialist expert in FHIR R4 and SNOMED-CT."),
                HumanMessage(content=prompt)
            ])
            
            content = response.content
            if "{" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                return json.loads(content[start:end])
            return {"raw_fhir": content}

        except Exception as e:
            logger.error(f"FHIR generation error: {e}")
            return {"error": str(e)}

    def build_hl7_v2(self, interaction_data: Dict[str, Any]):
        """
        Generates a standard HL7 v2.5.1 MSH/PID/OBR/OBX message.
        """
        logger.info("--- INTEROP: GENERATING HL7 v2 MESSAGE ---")
        
        prompt_entry = PROMPT_REGISTRY.get("MED-INT-HL7-001")
        if not prompt_entry:
            return {"error": "HL7 prompt not found."}

        prompt = prompt_entry.content.format(
            interaction_data=json.dumps(interaction_data, indent=2)
        )

        try:
            response = self.llm.invoke([
                SystemMessage(content="You are a certified HL7 Integration Engine specialist."),
                HumanMessage(content=prompt)
            ])
            
            return response.content

        except Exception as e:
            logger.error(f"HL7 generation error: {e}")
            return f"ERROR: {str(e)}"

    def validate_interop(self, data: str, format: str):
        """
        Basic structure validation for generated messages.
        """
        if format == "fhir":
            try:
                json.loads(data)
                return True
            except: return False
        elif format == "hl7":
            return "MSH|" in data and "PID|" in data
        return False
