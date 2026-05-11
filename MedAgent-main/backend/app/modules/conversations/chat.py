"""Streaming chat endpoint with MedAgent integration."""

import json
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.core.config import settings
from app.core.deps import get_current_user, limiter
from app.modules.conversations.schemas import ChatRequest
from app.modules.conversations.service import (
    add_message,
    get_conversation,
    get_messages,
    update_triage,
)

chat_router = APIRouter(prefix="/conversations", tags=["chat"])

_agent = None


def _create_vision_provider():
    """Build a VisionProvider from settings. Returns None if no provider is configured.

    Resolution order:
      1. VISION_PROVIDER setting → openrouter | openai | groq | gemini | disabled
      2. Falls back to OpenRouter if LLM_API_KEY exists
      3. Falls back to OpenAI if OPENAI_API_KEY exists
    """
    from app.ai.llm.vision_provider import VisionProvider

    explicit = (settings.VISION_PROVIDER or "").lower()
    model = settings.VISION_MODEL or "openai/gpt-4o"

    if explicit == "disabled":
        return None

    if explicit == "openai" or (not explicit and os.environ.get("OPENAI_API_KEY")):
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if api_key:
            return VisionProvider(
                base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                api_key=api_key,
                model=model,
            )

    if explicit == "gemini" and os.environ.get("GEMINI_API_KEY"):
        return VisionProvider(
            base_url=os.environ.get(
                "GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai"
            ),
            api_key=os.environ.get("GEMINI_API_KEY", ""),
            model=model,
        )

    # Default: OpenRouter (single key for many vision-capable models)
    api_key = settings.LLM_API_KEY or os.environ.get("OPENROUTER_API_KEY", "")
    if api_key:
        return VisionProvider(
            base_url=settings.LLM_BASE_URL,
            api_key=api_key,
            model=model,
        )
    return None


def _register_vision_tool(registry):
    """Register the analyze_vision tool with a configured vision provider."""
    try:
        from app.ai.tools.analyze_vision import AnalyzeVisionTool

        provider = _create_vision_provider()
        registry.register(AnalyzeVisionTool(vision_provider=provider))
    except Exception:
        pass


def _build_agent(llm):
    """Build a fresh MedAgent with the given LLM — mirrors _get_agent but skips DB wiring."""
    from app.ai.agent.agent import MedAgent
    from app.ai.agent.registry import ToolRegistry
    from app.ai.tools.red_flag_detector import DetectRedFlagsTool

    registry = ToolRegistry()
    registry.register(DetectRedFlagsTool())
    _register_vision_tool(registry)

    # Register stateless tools (no DB required)
    try:
        from app.ai.tools.triage_scorer import ScoreTriageTool

        registry.register(ScoreTriageTool())
    except Exception:
        pass

    try:
        from app.ai.tools.medication import CheckMedicationTool

        registry.register(CheckMedicationTool())
    except Exception:
        pass

    try:
        from app.ai.tools.mental_health import ScreenMentalHealthTool

        registry.register(ScreenMentalHealthTool())
    except Exception:
        pass

    try:
        from app.ai.tools.assess_pediatric_safety import AssessPediatricSafetyTool

        registry.register(AssessPediatricSafetyTool())
    except Exception:
        pass

    try:
        from app.ai.tools.assess_pregnancy_safety import AssessPregnancySafetyTool

        registry.register(AssessPregnancySafetyTool())
    except Exception:
        pass

    try:
        from app.ai.tools.calibrate_uncertainty import CalibrateUncertaintyTool

        registry.register(CalibrateUncertaintyTool())
    except Exception:
        pass

    try:
        from app.ai.tools.doctor_summary import SummarizeForDoctorTool

        summary_tool = SummarizeForDoctorTool()
        summary_tool.set_llm(llm)
        registry.register(summary_tool)
    except Exception:
        pass

    try:
        from app.ai.tools.tot_differential_diagnosis import ToTDifferentialDiagnosisTool

        registry.register(ToTDifferentialDiagnosisTool(llm))
    except Exception:
        pass

    try:
        from app.ai.tools.format_soap import FormatSOAPTool

        registry.register(FormatSOAPTool(llm))
    except Exception:
        pass

    return MedAgent(llm=llm, registry=registry)


def _create_llm(model_override: str | None = None):
    """Factory: create LLM provider, auto-routing by model prefix.

    Prefix convention:
      groq/    → Groq (OpenAI-compatible, free tier)
      oa/      → OpenAI direct
      gemini/  → Google Gemini (OpenAI-compatible endpoint)
      hf/      → HuggingFace Inference API
      (no prefix) → OpenRouter (default)
    """
    model = model_override or settings.LLM_MODEL

    from app.ai.llm.openai_compat import OpenAICompatProvider

    # ── Groq ──
    if model.startswith("groq/"):
        actual = model.replace("groq/", "", 1)
        return OpenAICompatProvider(
            base_url=os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
            api_key=os.environ.get("GROQ_API_KEY", ""),
            model=actual,
        )

    # ── OpenAI direct ──
    if model.startswith("oa/"):
        actual = model.replace("oa/", "", 1)
        return OpenAICompatProvider(
            base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            api_key=os.environ.get("OPENAI_API_KEY", ""),
            model=actual,
        )
    if model.startswith("openai/"):
        actual = model.replace("openai/", "", 1)
        return OpenAICompatProvider(
            base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            api_key=os.environ.get("OPENAI_API_KEY", ""),
            model=actual,
        )

    # ── Google Gemini (OpenAI-compatible endpoint) ──
    if model.startswith("gemini/"):
        actual = model.replace("gemini/", "", 1)
        return OpenAICompatProvider(
            base_url=os.environ.get(
                "GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai"
            ),
            api_key=os.environ.get("GEMINI_API_KEY", ""),
            model=actual,
        )

    # ── HuggingFace Inference ──
    if model.startswith("hf/"):
        actual = model.replace("hf/", "", 1)
        from app.ai.llm.hf_inference import HfInferenceProvider

        return HfInferenceProvider(
            base_url=f"https://api-inference.huggingface.co/models/{actual}",
            api_key=os.environ.get("HF_API_KEY", ""),
        )

    # ── Default: OpenRouter ──
    return OpenAICompatProvider(
        base_url=settings.LLM_BASE_URL,
        api_key=settings.LLM_API_KEY,
        model=model,
    )


def _get_agent():
    """Initialize or return the singleton MedAgent with all tools wired."""
    global _agent
    if _agent is not None:
        return _agent

    from app.ai.agent.agent import MedAgent
    from app.ai.agent.registry import ToolRegistry
    from app.ai.tools.red_flag_detector import DetectRedFlagsTool

    registry = ToolRegistry()

    # Register stateless tools first
    registry.register(DetectRedFlagsTool())
    _register_vision_tool(registry)

    # Try to register tools that need external deps
    try:
        import asyncio

        from app.ai.retrieval.retriever import Retriever
        from app.ai.retrieval.vectorstore import VectorStore
        from app.ai.tools.doctor_summary import SummarizeForDoctorTool
        from app.ai.tools.retrieve_knowledge import RetrieveKnowledgeTool
        from app.ai.tools.triage_scorer import ScoreTriageTool

        llm = _create_llm()

        # Retriever needs a VectorStore with real DB session
        # For now, skip if no DB (agent will work without retrieval)
        async def _wire():
            try:
                from app.core.database import get_session

                async with get_session() as session:
                    store = VectorStore(session)
                    retriever = Retriever(store)
                    registry.register(RetrieveKnowledgeTool(retriever))
            except Exception:
                pass

        asyncio.get_event_loop().run_until_complete(_wire())

        registry.register(ScoreTriageTool())

        # ── Medication checker ──
        try:
            from app.ai.tools.medication import CheckMedicationTool

            registry.register(CheckMedicationTool())
        except Exception:
            pass

        # ── Mental health screener ──
        try:
            from app.ai.tools.mental_health import ScreenMentalHealthTool

            registry.register(ScreenMentalHealthTool())
        except Exception:
            pass

        # ── Pediatric safety ──
        try:
            from app.ai.tools.assess_pediatric_safety import AssessPediatricSafetyTool

            registry.register(AssessPediatricSafetyTool())
        except Exception:
            pass

        # ── Pregnancy safety ──
        try:
            from app.ai.tools.assess_pregnancy_safety import AssessPregnancySafetyTool

            registry.register(AssessPregnancySafetyTool())
        except Exception:
            pass

        # ── Calibrate uncertainty ──
        try:
            from app.ai.tools.calibrate_uncertainty import CalibrateUncertaintyTool

            registry.register(CalibrateUncertaintyTool())
        except Exception:
            pass

        summary_tool = SummarizeForDoctorTool()
        summary_tool.set_llm(llm)
        registry.register(summary_tool)

        # ── Register ToT tool ──
        try:
            from app.ai.tools.tot_differential_diagnosis import ToTDifferentialDiagnosisTool

            tot_tool = ToTDifferentialDiagnosisTool(llm)
            registry.register(tot_tool)
        except Exception:
            pass

        # ── Register SOAP formatter ──
        try:
            from app.ai.tools.format_soap import FormatSOAPTool

            soap_tool = FormatSOAPTool(llm)
            registry.register(soap_tool)
        except Exception:
            pass

        # ── إنشاء verifier LLM للبوابة الأمان ──
        # بنستخدم نفس الموديل لكن temperature=0 للدقة (مفيش إبداع في التدقيق)
        verifier = _create_verifier() if not os.environ.get("DISABLE_SAFETY_GATE") else None

        _agent = MedAgent(llm=llm, registry=registry, verifier=verifier)
    except Exception:
        # Fallback: agent with only red-flag detector
        try:
            llm = _create_llm()
            _agent = MedAgent(llm=llm, registry=registry)
        except Exception:
            _agent = MedAgent(
                llm=_create_llm(),
                registry=registry,
            )

    return _agent


def _create_verifier():
    """
    ينشئ HallucinationVerifier — مدقق هلاوس منفصل.

    بنستخدم نفس الـ provider لكن temperature=0.
    ممكن تستخدم env var `VERIFIER_MODEL` لتحديد موديل أصغر وأسرع.
    """
    from app.ai.tools.verify_no_hallucination import HallucinationVerifier

    verifier_model = settings.VERIFIER_MODEL
    if verifier_model:
        # موديل منفصل للمدقق
        from app.ai.llm.openai_compat import OpenAICompatProvider

        verifier_llm = OpenAICompatProvider(
            base_url=settings.LLM_BASE_URL,
            api_key=settings.LLM_API_KEY,
            model=verifier_model,
        )
    else:
        # نفس الموديل الأساسي (default)
        verifier_llm = _create_llm()

    return HallucinationVerifier(verifier_llm)


@chat_router.post("/{conv_id}/chat")
@limiter.limit("20/minute")
async def chat(
    request: Request,
    conv_id: uuid.UUID,
    body: ChatRequest,
    current_user: dict = Depends(get_current_user),
):
    """Send a message and stream the agent's response via SSE."""
    user_id = uuid.UUID(current_user["sub"])
    conv = await get_conversation(conv_id, user_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await add_message(conv_id, role="user", content=body.message)

    history_msgs = await get_messages(conv_id)
    history = [{"role": m.role, "content": m.text} for m in history_msgs[:-1]]

    # Use model override if specified, otherwise use cached agent
    if body.model:
        llm = _create_llm(body.model)
        agent = _build_agent(llm)
        # Update conversation title to show model name
        if not conv.title:
            model_label = (
                body.model.replace("groq/", "")
                .replace("oa/", "")
                .replace("gemini/", "")
                .replace("hf/", "")
            )
            try:
                conv.title = model_label[:100]
                from app.core.database import get_session

                async with get_session() as session:
                    session.add(conv)
                    await session.commit()
            except Exception:
                pass
    else:
        agent = _get_agent()

    async def stream():
        assistant_content = ""
        # Collect citations from tool results for enforcement
        citation_sources: list[dict] = []
        # نتيجة بوابة الأمان (بتتملي لو الـ safety gate اشتغل)
        safety_data: dict | None = None

        async for event in agent.run(
            user_message=body.message,
            conversation_history=history,
            language=conv.language,
            conversation_id=str(conv_id),
            image_data=body.image_data,
            image_kind=body.image_kind,
        ):
            # Collect citations from retrieve_knowledge results
            if (
                event.type == "tool_result"
                and event.data.get("tool") == "retrieve_medical_knowledge"
            ):
                result = event.data.get("result", {})
                for chunk in result.get("chunks", []):
                    citation_sources.append(
                        {
                            "source": chunk.get("source", ""),
                            "title": chunk.get("title", ""),
                            "url": chunk.get("url", ""),
                        }
                    )

            # Emit citation events alongside tokens
            if event.type == "token" and citation_sources:
                # Yield citations as a separate event type
                sse_data = json.dumps(
                    {"type": "citations", "data": {"sources": citation_sources[-3:]}}
                )
                yield f"data: {sse_data}\n\n"
                citation_sources = []  # Only send once per batch

            sse_data = json.dumps(event.model_dump())
            yield f"data: {sse_data}\n\n"

            if event.type == "token":
                assistant_content += event.content
            elif event.type == "triage":
                await update_triage(
                    conv_id,
                    level=event.data.get("level", "routine"),
                    score=event.data.get("score"),
                    red_flags=event.data.get("flags"),
                )
            elif event.type == "red_flag":
                await update_triage(
                    conv_id,
                    level="emergency",
                    red_flags=event.data.get("flags", []),
                    set_flagged=True,
                )
            elif event.type == "safety":
                # حفظ تقييم السلامة في الداتابيز بعد حفظ الرسالة
                safety_data = event.data
                yield f"data: {json.dumps({'type': 'safety', 'data': safety_data})}\n\n"

        if assistant_content:
            msg = await add_message(
                conv_id, role="assistant", content=assistant_content, citations=citation_sources
            )

            # ── حفظ تقييم السلامة ──
            if safety_data:
                await _save_safety_assessment(msg.id, safety_data)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _save_safety_assessment(message_id: uuid.UUID, safety_data: dict) -> None:
    """
    يحفظ نتيجة تقييم السلامة في جدول safety_assessments.

    بنستخدم assessment_to_db عشان نحول dict البوابة لشكل جاهز للـ INSERT.
    """
    from app.core.database import get_session
    from app.models.safety_assessment import SafetyAssessment

    assessment = safety_data.get("assessment", {})
    db_data = SafetyAssessment(
        message_id=message_id,
        hallucination_score=assessment.get("hallucination_score"),
        citation_completeness=assessment.get("citation_completeness"),
        calibration_metadata=assessment.get("claims"),
        triage_consistent=True,
    )

    try:
        async with get_session() as session:
            session.add(db_data)
            await session.commit()
    except Exception:
        # Fail silently — مش هنوقف الـ request بسبب فشل حفظ التقييم
        # الـ assessment بيكون already اتبعت للـ frontend في الـ SSE
        pass
