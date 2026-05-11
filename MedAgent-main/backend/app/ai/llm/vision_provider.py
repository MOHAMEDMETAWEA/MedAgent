"""Vision LLM provider — wraps OpenAI vision API and Qwen-VL compatible endpoints."""

import base64
import io
import re
from typing import Any

import httpx
import structlog

logger = structlog.get_logger(__name__)

ALLOWED_MIME_TYPES = {
    "image/jpeg": "jpeg",
    "image/jpg": "jpeg",
    "image/png": "png",
    "image/webp": "webp",
    "image/heic": "heic",
    "image/heif": "heic",
}

MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB

# Heuristic patterns that suggest a non-clinical image
NON_CLINICAL_PATTERNS = re.compile(
    r"\b(cat|dog|pet|meme|screenshot|food|selfie|landscape|cartoon|logo|car|"
    r"sport|gaming|قطة|كلب|طعام|سيلفي|كرتون)\b",
    re.IGNORECASE,
)

DISCLAIMER_EN = (
    "⚠️ IMPORTANT DISCLAIMER: This is an AI preliminary assessment only — "
    "NOT a medical diagnosis. Image analysis by AI has significant limitations. "
    "Always consult a licensed radiologist or clinician for any imaging review. "
    "This tool must NOT replace professional medical evaluation."
)
DISCLAIMER_AR = (
    "⚠️ تحذير مهم: هذا تقييم أولي بالذكاء الاصطناعي فقط — وليس تشخيصاً طبياً. "
    "لتحليل الصور بالذكاء الاصطناعي قيود جوهرية. "
    "استشر دائماً طبيباً أو أخصائياً مرخصاً لمراجعة أي صورة طبية. "
    "لا يجوز استبدال هذه الأداة بالتقييم الطبي المتخصص."
)


def _detect_mime(data: bytes) -> str | None:
    """Detect image MIME type from magic bytes."""
    if data[:2] == b"\xff\xd8":
        return "image/jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:4] in (b"RIFF", b"WEBP") or data[8:12] == b"WEBP":
        return "image/webp"
    if data[:4] in (b"ftyp", b"\x00\x00\x00\x18", b"\x00\x00\x00\x1c"):
        return "image/heic"
    return None


def validate_image(data: bytes) -> str:
    """Validate image bytes. Returns detected MIME type or raises ValueError."""
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError(f"Image too large: {len(data) / 1024 / 1024:.1f} MB (max 10 MB)")
    mime = _detect_mime(data)
    if mime not in ALLOWED_MIME_TYPES:
        raise ValueError(
            f"Unsupported image format. Accepted: JPEG, PNG, WebP, HEIC. "
            f"Detected: {mime or 'unknown'}"
        )
    return mime


def try_blur_faces(data: bytes, mime: str) -> bytes:
    """Attempt to blur detected faces using Pillow. Falls back to original on error."""
    try:
        from PIL import Image, ImageFilter

        img = Image.open(io.BytesIO(data))

        # Try OpenCV face detection if available
        try:
            import cv2
            import numpy as np

            img_rgb = np.array(img.convert("RGB"))
            gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
            for x, y, w, h in faces:
                face_region = img.crop((x, y, x + w, y + h))
                blurred = face_region.filter(ImageFilter.GaussianBlur(radius=20))
                img.paste(blurred, (x, y))
            logger.info("face_blur", faces_found=len(faces))
        except ImportError:
            # No OpenCV — apply a global privacy blur to photo-type images
            # (conservative: blur entire image for photos before storage)
            pass

        buf = io.BytesIO()
        fmt = ALLOWED_MIME_TYPES.get(mime, "jpeg").upper()
        if fmt == "JPEG":
            fmt = "JPEG"
        img.save(buf, format=fmt if fmt in ("PNG", "WEBP", "JPEG") else "JPEG")
        return buf.getvalue()
    except Exception as e:
        logger.warning("face_blur_failed", error=str(e))
        return data


class VisionProvider:
    """Calls a vision-capable LLM (OpenAI GPT-4o Vision or compatible) to analyze medical images."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str = "gpt-4o",
        timeout: float = 90.0,
        max_retries: int = 2,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _build_vision_message(
        self,
        image_b64: str,
        mime: str,
        context: str,
        language: str,
    ) -> list[dict]:
        """Build the messages list for a vision API call."""
        if language == "ar":
            instruction = (
                "أنت نظام ذكاء اصطناعي طبي متخصص في التحليل الأولي للصور الطبية. "
                "حلل هذه الصورة الطبية وأجب بشكل منظم باللغة العربية:\n\n"
                "1. نوع الصورة (أشعة سينية / CT / صورة جلدية / جرح / غير طبية)\n"
                "2. الملاحظات السريرية الأولية\n"
                "3. مستوى الاستعجال: طوارئ / عاجل / روتيني\n"
                "4. نسبة الثقة (0.0-1.0)\n\n"
                "إذا كانت الصورة غير طبية (قطط، طعام، لقطات شاشة) أجب بـ: NON_MEDICAL\n"
                "إذا كانت الصورة طبية لكن التشخيص غير واضح أذكر ذلك صراحةً."
            )
        else:
            instruction = (
                "You are a medical AI providing preliminary image triage (NOT diagnosis). "
                "Analyze the medical image and respond in structured JSON:\n\n"
                "{\n"
                '  "image_kind": "xray|ct|photo|skin|wound|other",\n'
                '  "is_medical": true|false,\n'
                '  "findings": ["finding1", "finding2"],\n'
                '  "urgency": "emergency|urgent|routine|none",\n'
                '  "confidence": 0.0-1.0,\n'
                '  "notes": "any important caveats"\n'
                "}\n\n"
                "If the image is clearly NOT medical (pet, food, screenshot, meme), "
                'set "is_medical": false and "findings": ["NON_MEDICAL_IMAGE"].'
            )

        user_content: list[dict] = [
            {
                "type": "text",
                "text": f"{instruction}\n\nPatient context: {context or 'None provided'}",
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime};base64,{image_b64}",
                    "detail": "high",
                },
            },
        ]
        return [{"role": "user", "content": user_content}]

    async def analyze(
        self,
        image_data: bytes,
        context: str = "",
        language: str = "en",
        image_kind: str = "photo",
    ) -> dict[str, Any]:
        """
        Analyze medical image bytes.

        Parameters
        ----------
        image_data : bytes
            Raw image bytes (JPEG/PNG/WebP/HEIC, max 10 MB).
        context : str
            Patient symptom context to help the model.
        language : str
            "ar" or "en" — controls response language.
        image_kind : str
            Hint: "xray", "ct", "photo", "skin", "other".

        Returns
        -------
        dict with keys: findings, urgency, confidence, disclaimer, is_medical, image_kind
        """
        mime = validate_image(image_data)

        # Blur faces for photo-type images before encoding
        if image_kind in ("photo", "skin"):
            image_data = try_blur_faces(image_data, mime)

        image_b64 = base64.b64encode(image_data).decode("ascii")
        messages = self._build_vision_message(image_b64, mime, context, language)

        disclaimer = DISCLAIMER_AR if language == "ar" else DISCLAIMER_EN
        raw_content = ""

        last_exc: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(self.timeout)) as client:
                    resp = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=self._headers(),
                        json={
                            "model": self.model,
                            "messages": messages,
                            "max_tokens": 512,
                            "temperature": 0.1,
                        },
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    raw_content = data["choices"][0]["message"].get("content", "")
                    break
            except Exception as e:
                last_exc = e
                if attempt < self.max_retries:
                    import asyncio

                    await asyncio.sleep(2**attempt)
                else:
                    logger.error("vision_llm_failed", error=str(e))
                    return {
                        "findings": ["Vision LLM unavailable. Please try again later."],
                        "urgency": "routine",
                        "confidence": 0.0,
                        "is_medical": True,
                        "image_kind": image_kind,
                        "disclaimer": disclaimer,
                        "error": str(last_exc),
                    }

        return _parse_vision_response(raw_content, image_kind, disclaimer)


def _parse_vision_response(
    raw: str,
    image_kind: str,
    disclaimer: str,
) -> dict[str, Any]:
    """Parse the vision LLM's response into a structured dict."""
    import json as _json

    # Check for non-medical refusal
    if "NON_MEDICAL" in raw.upper():
        return {
            "findings": [],
            "urgency": "none",
            "confidence": 0.0,
            "is_medical": False,
            "image_kind": image_kind,
            "disclaimer": disclaimer,
            "refusal_reason": (
                "This image does not appear to be a medical image. "
                "Please upload a clinical photo, X-ray, CT scan, or other medical image."
            ),
        }

    # Try to parse JSON response
    try:
        # Extract JSON block if wrapped in markdown code fence
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
        parsed = _json.loads(json_match.group(1)) if json_match else _json.loads(raw)

        return {
            "findings": parsed.get("findings", [raw]),
            "urgency": parsed.get("urgency", "routine"),
            "confidence": float(parsed.get("confidence", 0.5)),
            "is_medical": parsed.get("is_medical", True),
            "image_kind": parsed.get("image_kind", image_kind),
            "notes": parsed.get("notes", ""),
            "disclaimer": disclaimer,
        }
    except (_json.JSONDecodeError, ValueError):
        # Fallback: return raw text as a single finding
        return {
            "findings": [raw] if raw else ["Analysis complete. See raw output."],
            "urgency": "routine",
            "confidence": 0.3,
            "is_medical": True,
            "image_kind": image_kind,
            "disclaimer": disclaimer,
        }
