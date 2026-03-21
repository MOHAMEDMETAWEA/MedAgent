"""
Common medical terms and their patient-friendly translations.
"""

MEDICAL_TERMS = {
    "hypertension": "high blood pressure",
    "myocardial infarction": "heart attack",
    "gastroenteritis": "stomach infection",
    "dyspnea": "difficulty breathing",
    "erythema": "redness of the skin",
    "hematoma": "bruise or swelling of clotted blood",
    "pharyngitis": "throat infection",
    "tachycardia": "fast heart rate",
    "bradycardia": "slow heart rate",
    "hypotension": "low blood pressure",
    "edema": "swelling caused by fluid",
    "pruritus": "itching",
    "syncope": "fainting or passing out",
    "vertigo": "dizziness or spinning sensation",
    "alopecia": "hair loss",
    "epistaxis": "nosebleed",
    "insomnia": "trouble sleeping",
    "myalgia": "muscle pain",
    "arthralgia": "joint pain",
    "rhinitis": "stuffy or runny nose",
    "xerostomia": "dry mouth",
    "dysphagia": "difficulty swallowing",
    "gastritis": "inflammation of the stomach lining",
    "stomatitis": "mouth sores",
    "conjunctivitis": "pink eye",
    "otitis": "ear infection",
    "pneumonia": "lung infection",
    "bronchitis": "infection of the breathing tubes",
    "analgesic": "pain reliever",
    "antipyretic": "fever reducer",
    "diuretic": "water pill",
    "anticoagulant": "blood thinner",
    "metastasis": "spread of cancer",
    "benign": "non-cancerous",
    "malignant": "cancerous",
}


def translate_term(term: str) -> str:
    """Returns a simple explanation for a technical term if available."""
    return MEDICAL_TERMS.get(term.lower(), term)


def explain_text(text: str, replace_only: bool = False) -> str:
    """
    Replaces medical terms in text using a single-pass regex to avoid double-replacement.
    Preserves original casing and supports 'replace_only' mode.
    """
    import re

    if not text:
        return text

    # Sort keys to ensure longer terms are matched first (e.g., 'heart attack' before 'heart')
    sorted_terms = sorted(MEDICAL_TERMS.keys(), key=len, reverse=True)
    pattern_string = (
        r"\b(" + "|".join(re.escape(term) for term in sorted_terms) + r")\b"
    )
    pattern = re.compile(pattern_string, re.IGNORECASE)

    def replace_fn(match):
        original = match.group(0)
        term_key = original.lower()
        explanation = MEDICAL_TERMS.get(term_key, original)

        if replace_only:
            # Match the first letter's casing
            if original[0].isupper():
                return explanation.capitalize()
            return explanation
        else:
            return f"{original} ({explanation})"

    return pattern.sub(replace_fn, text)
