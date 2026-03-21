"""
Bias & Safety Monitor - detects demographic bias and hallucinated clinical facts.
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class BiasMonitor:
    @staticmethod
    def detect_demographic_bias(content: str, profile: Dict) -> Dict:
        """Checks if the output contains stereotypical or biased language based on age/gender."""
        age = profile.get("age", "Unknown")
        gender = profile.get("gender", "Unknown")

        # Simple heuristic check for demographic mentions
        findings = []
        if (
            gender.lower() == "female"
            and "pregnancy" not in content.lower()
            and "hysteria" in content.lower()
        ):
            findings.append("Potential gender bias: Outdated term detected.")

        return {
            "has_bias": len(findings) > 0,
            "findings": findings,
            "severity": "High" if len(findings) > 0 else "None",
        }

    @staticmethod
    def verify_fact_consistency(diagnosis: str, evidence: List[str]) -> bool:
        """Cross-references the diagnosis with the provided evidence sources."""
        # This would typically use an LLM or a knowledge graph in production
        diagnosis_terms = set(diagnosis.lower().split())
        evidence_content = " ".join(evidence).lower()

        overlap = [term for term in diagnosis_terms if term in evidence_content]
        return len(overlap) > 0
