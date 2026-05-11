"""Tool: detect_red_flags — emergency symptom detection for patient safety."""

# Path: للوصول لملف YAML
# yaml: لقراءة ملف YAML
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from app.ai.agent.base import Tool

# ── Schema ──


class RedFlagInput(BaseModel):
    """Input schema for red flag detection."""

    text: str = Field(
        ...,
        min_length=1,
        description="Patient message text to check for emergency keywords",
    )


# ── Detector Logic ──


class RedFlagDetector:
    """
    # محرك كشف الـ red flags — بيفحص النص ضد قوائم الكلمات المفتاحية.
    #
    # بيقرأ red_flags_keywords.yaml أول مرة بس (lazy loading).
    # بيدعم عربي + إنجليزي.
    """

    _keywords = None  # cached — بيتحمل مرة واحدة

    @classmethod
    def _load_keywords(cls) -> dict:
        """Load keyword data from YAML file (cached)."""
        if cls._keywords is not None:
            return cls._keywords

        # بنبني المسار من الـ safety folder
        yaml_path = Path(__file__).resolve().parent.parent / "safety" / "red_flags_keywords.yaml"
        with open(yaml_path, encoding="utf-8") as f:
            cls._keywords = yaml.safe_load(f)
        return cls._keywords

    def detect(self, text: str) -> dict[str, Any]:
        """
        # يفحص النص ويعيد نتيجة الكشف.
        #
        # بيدور على الكلمات المفتاحية في النص (case-insensitive).
        # لو لقى emergency keyword — يرجع emergency فورًا.
        # لو لقى urgent بس — يرجع urgent.
        # لو في rule_patterns اتنين keywords مع بعض — يرجع emergency.
        """
        data = self._load_keywords()
        text_lower = text.lower()
        flags = []

        # 1. فحص emergency keywords
        for lang in ("en", "ar"):
            for keyword in data["emergency_keywords"][lang]:
                if keyword.lower() in text_lower:
                    flags.append(
                        {
                            "keyword": keyword,
                            "language": lang,
                            "level": "emergency",
                        }
                    )

        # 2. فحص urgent keywords — بس لو مفيش emergency
        if not flags:
            for lang in ("en", "ar"):
                for keyword in data["urgent_keywords"][lang]:
                    if keyword.lower() in text_lower:
                        flags.append(
                            {
                                "keyword": keyword,
                                "language": lang,
                                "level": "urgent",
                            }
                        )

        # 3. فحص rule_patterns — كلمتين مع بعض = emergency
        for rule in data.get("rule_patterns", []):
            # كل الكلمات المطلوبة في النص؟
            if all(kw.lower() in text_lower for kw in rule["keywords"]):
                # نتجنب التكرار — لو الكلمة موجودة في flags already
                already = [f["keyword"] for f in flags]
                if not any(kw in already for kw in rule["keywords"]):
                    flags.insert(
                        0,
                        {
                            "keyword": " + ".join(rule["keywords"]),
                            "language": "rule",
                            "level": rule["level"],
                        },
                    )

        # 4. تحديد الـ severity النهائي
        has_emergency = any(f["level"] == "emergency" for f in flags)
        has_red_flag = len(flags) > 0

        return {
            "has_red_flag": has_red_flag,
            "flags": flags,
            "severity": ("emergency" if has_emergency else ("urgent" if has_red_flag else "none")),
        }


# ── Tool ──


class DetectRedFlagsTool(Tool):
    """Scans patient messages for emergency keywords and returns red-flag status."""

    def __init__(self):
        self._detector = RedFlagDetector()

    @property
    def name(self) -> str:
        return "detect_red_flags"

    @property
    def description(self) -> str:
        return (
            "Scan the patient's message for emergency keywords (chest pain radiating, "
            "stroke FAST signs, severe bleeding, anaphylaxis, suicidal ideation, "
            "respiratory distress, sepsis red flags). Returns has_red_flag boolean "
            "and severity level. Use BEFORE any other response."
        )

    @property
    def input_schema(self) -> type[BaseModel]:
        return RedFlagInput

    async def run(self, input_data: BaseModel) -> dict[str, Any]:
        """Execute red flag detection on the input text."""
        if not isinstance(input_data, RedFlagInput):
            raise TypeError(f"Expected RedFlagInput, got {type(input_data)}")

        return self._detector.detect(input_data.text)
