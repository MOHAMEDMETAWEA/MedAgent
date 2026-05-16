"""Tool: detect_red_flags — emergency symptom detection for patient safety."""

# Path: للوصول لملف YAML
# yaml: لقراءة ملف YAML
from pathlib import Path
from typing import Any
import json
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
    AI_TRIAGE_PROMPT = """You are a highly sensitive Clinical Safety Agent. Your ONLY job is to analyze the patient's message (which may be in English, Arabic, or Egyptian slang) and determine if it contains life-threatening emergency symptoms or urgent medical situations.
Focus on semantics, context, and severity, not exact keywords. 

Examples of EMERGENCY symptoms: crushing chest pain, radiating pain to arm/jaw/shoulder, "حجر على صدري", severe shortness of breath, "مش قادر آخد نفسي", signs of stroke (facial drooping, sudden weakness), severe bleeding, anaphylaxis, suicidal ideation.

Respond ONLY with a valid JSON object and absolutely nothing else. Do not use markdown blocks like ```json.
Format required:
{
    "has_red_flag": true or false,
    "severity": "emergency" or "urgent" or "none",
    "flags": [
        {
            "keyword": "extract the symptom phrase from the user's text",
            "language": "ar" or "en",
            "level": "emergency" or "urgent"
        }
    ]
}"""

    async def detect_with_ai(self, text: str, llm_provider) -> dict[str, Any]:
        """
        AI Semantic Triage: بيفهم السياق والعامية باستخدام الموديل.
        لو الموديل فشل، بينفذ دالة detect القديمة (YAML Fallback).
        """
        messages = [
            {"role": "system", "content": self.AI_TRIAGE_PROMPT},
            {"role": "user", "content": text}
        ]
        
        try:
            accumulated_json = ""
            # بنستخدم نفس الـ LLM Provider بتاعك
            async for event in llm_provider.generate_stream(
                messages=messages,
                tools=None, # مفيش أدوات هنا عشان ننجز
                max_tokens=250,
                temperature=0.0 # صفر عشان التقييم الطبي يكون صارم بدون هلوسة
            ):
                if event["type"] == "token":
                    accumulated_json += event["content"]
            
            # تنظيف الـ JSON من أي مخرجات غريبة
            clean_json = accumulated_json.replace("```json", "").replace("```", "").strip()
            result = json.loads(clean_json)
            
            # التأكد إن الـ Format رجع صح وفيه المفاتيح الأساسية
            if "has_red_flag" in result and "severity" in result:
                return result
                
        except Exception as e:
            print(f"⚠️ AI Red Flag Triage failed (falling back to YAML): {e}")
            pass 
            
        # Fallback: لو الـ AI رد بـ Format غلط أو حصل إيرور، شغل הـ YAML القديم
        return self.detect(text)

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
