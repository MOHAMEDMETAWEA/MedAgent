"""
Generic Provider Management System
Handles provider/specialty assignment without hard-coded dependencies.
"""
from typing import Dict, List
from enum import Enum
import random


class Specialty(Enum):
    """Medical specialties - generic and extensible."""
    CARDIOLOGY = "cardiology"
    NEUROLOGY = "neurology"
    EMERGENCY = "emergency"
    GENERAL = "general"
    RESPIRATORY = "respiratory"
    GASTROENTEROLOGY = "gastroenterology"
    ENDOCRINOLOGY = "endocrinology"
    INFECTIOUS_DISEASE = "infectious_disease"

class ProviderManager:
    """
    Generic provider management system.
    Can be extended with actual provider APIs or databases.
    """
    
    def __init__(self):
        self.providers: Dict[Specialty, List[str]] = {}
        self._initialize_default_providers()
    
    def _initialize_default_providers(self):
        """Initialize with generic provider templates (not specific names)."""
        # Generic provider templates - can be replaced with actual provider data
        self.providers = {
            Specialty.CARDIOLOGY: ["Cardiology Specialist", "Cardiologist"],
            Specialty.NEUROLOGY: ["Neurology Specialist", "Neurologist"],
            Specialty.EMERGENCY: ["Emergency Care Team", "Emergency Response Unit"],
            Specialty.GENERAL: ["General Practitioner", "Primary Care Physician"],
            Specialty.RESPIRATORY: ["Respiratory Specialist", "Pulmonologist"],
            Specialty.GASTROENTEROLOGY: ["Gastroenterology Specialist", "Gastroenterologist"],
            Specialty.ENDOCRINOLOGY: ["Endocrinology Specialist", "Endocrinologist"],
            Specialty.INFECTIOUS_DISEASE: ["Infectious Disease Specialist", "ID Specialist"],
        }
    
    def add_provider(self, specialty: Specialty, provider_name: str):
        """Add a provider to a specialty."""
        if specialty not in self.providers:
            self.providers[specialty] = []
        if provider_name not in self.providers[specialty]:
            self.providers[specialty].append(provider_name)
    
    def get_provider(self, specialty: Specialty) -> str:
        """Get a provider for a specialty (generic selection)."""
        if specialty in self.providers and self.providers[specialty]:
            return random.choice(self.providers[specialty])
        return "Available Healthcare Provider"
    
    def determine_specialty_from_diagnosis(self, diagnosis: str) -> Specialty:
        """
        Determine appropriate specialty from diagnosis text.
        Uses keyword matching - can be enhanced with ML models.
        """
        diagnosis_lower = diagnosis.lower()
        
        # Emergency conditions
        emergency_keywords = ["infarction", "stroke", "sepsis", "appendicitis", 
                             "cardiac arrest", "trauma", "critical", "emergency"]
        if any(kw in diagnosis_lower for kw in emergency_keywords):
            return Specialty.EMERGENCY
        
        # Specialty-specific keywords
        if any(kw in diagnosis_lower for kw in ["heart", "cardio", "myocardial", "cardiac"]):
            return Specialty.CARDIOLOGY
        
        if any(kw in diagnosis_lower for kw in ["brain", "neuro", "stroke", "seizure", "neurological"]):
            return Specialty.NEUROLOGY
        
        if any(kw in diagnosis_lower for kw in ["lung", "respiratory", "pneumonia", "asthma", "breathing"]):
            return Specialty.RESPIRATORY
        
        if any(kw in diagnosis_lower for kw in ["stomach", "gastro", "digestive", "appendicitis", "abdomen"]):
            return Specialty.GASTROENTEROLOGY
        
        if any(kw in diagnosis_lower for kw in ["diabetes", "diabetic", "endocrine", "hormone"]):
            return Specialty.ENDOCRINOLOGY
        
        if any(kw in diagnosis_lower for kw in ["infection", "bacterial", "viral", "sepsis"]):
            return Specialty.INFECTIOUS_DISEASE
        
        return Specialty.GENERAL
    
    def get_appointment_details(self, specialty: Specialty, is_emergency: bool, 
                                diagnosis: str = "") -> Dict[str, str]:
        """
        Generate generic appointment details.
        Can be extended to integrate with actual scheduling systems.
        """
        provider = self.get_provider(specialty)
        
        if is_emergency:
            return {
                "priority": "URGENT - IMMEDIATE ESCALATION",
                "provider": provider,
                "timing": "IMMEDIATE - Seek emergency care immediately",
                "instructions": "Please proceed to the nearest emergency facility immediately. "
                              "If you are experiencing a life-threatening emergency, call your local emergency services."
            }
        else:
            return {
                "priority": "ROUTINE",
                "provider": provider,
                "timing": "Schedule within 24-48 hours",
                "instructions": "Please schedule an appointment with a healthcare provider. "
                              "This is not an emergency, but professional evaluation is recommended."
            }

# Global provider manager instance
provider_manager = ProviderManager()

