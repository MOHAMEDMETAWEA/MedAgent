"""MedAgent ReAct loop — connects LLM, tools, safety, and conversation streaming."""

import json
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from app.ai.agent.branches.pediatric import PediatricContext
from app.ai.agent.branches.pregnancy import PregnancyContext
from app.ai.agent.pii import scrub_pii
from app.ai.agent.registry import ToolRegistry
from app.ai.agent.tot_mode import ToTOrchestrator
from app.ai.llm.base import LLMProvider
from app.ai.safety.post_llm_gate import PostLLMSafetyGate
from app.ai.tools.red_flag_detector import RedFlagDetector
from app.ai.tools.verify_no_hallucination import HallucinationVerifier

MAX_ITERATIONS = 5


class AgentEvent(BaseModel):
    """Single event emitted by the agent during a conversation turn."""

    type: str  # "token", "tool_start", "tool_result", "triage", "red_flag", "done", "error"
    content: str = ""
    data: dict[str, Any] = {}


class MedAgent:
    """ReAct agent — thinks → acts → observes loop with tools and safety."""

    def __init__(
        self,
        llm: LLMProvider,
        registry: ToolRegistry,
        patient_age: int | None = None,
        patient_conditions: list[str] | None = None,
        patient_is_pregnant: bool = False,
        verifier: HallucinationVerifier | None = None,
    ):
        self.llm = llm
        self.registry = registry
        self.patient_age = patient_age
        self.patient_conditions = patient_conditions or []
        self.patient_is_pregnant = patient_is_pregnant
        self.red_flag_detector = RedFlagDetector()
        self._system_prompts: dict[str, str] = {}

        # بوابة الأمان (اختيارية — بتشتغل لو موجودة)
        self._safety_gate = PostLLMSafetyGate(verifier) if verifier else None

        # Build branch contexts once
        self._pediatric_ctx: PediatricContext | None = (
            PediatricContext.from_age_years(float(patient_age))
            if patient_age is not None and patient_age < 18
            else None
        )
        self._pregnancy_ctx: PregnancyContext | None = (
            PregnancyContext(trimester=None) if patient_is_pregnant else None
        )

    def _resolve_branch(self, user_message: str) -> None:
        """Auto-detect pregnancy branch from conversation text if not already set."""
        if self._pregnancy_ctx is None and self._pediatric_ctx is None:
            detected = PregnancyContext.detect_from_text(user_message)
            if detected:
                self._pregnancy_ctx = detected
                self.patient_is_pregnant = True

    def _load_system_prompt(self, language: str) -> str:
        """Load and format the system prompt for the given language and patient context."""
        if self._pediatric_ctx:
            key = self._pediatric_ctx.system_prompt_key(language)
        elif self._pregnancy_ctx or self.patient_is_pregnant:
            key = f"{language}_pregnancy"
        else:
            key = language

        if key not in self._system_prompts:
            prompts_dir = Path(__file__).resolve().parent / "prompts"
            filename = f"system_{key}.txt"
            if not (prompts_dir / filename).exists():
                filename = f"system_{language}.txt"
            with open(prompts_dir / filename, encoding="utf-8") as f:
                template = f.read()
            safety_override = (
                "\n\nCRITICAL INSTRUCTION: If the patient mentions taking ANY medications, pills, or drugs (e.g., Aspirin, Ibuprofen, etc.), "
                "you MUST immediately and strictly call the `check_medication_interactions` tool to verify safety BEFORE asking any further questions or giving advice."
            )
            template += safety_override
            self._system_prompts[key] = template.format(
                current_date=datetime.now(UTC).strftime("%Y-%m-%d"),
                patient_age=self.patient_age or "unknown",
                conditions=", ".join(self.patient_conditions) or "none reported",
            )
        return self._system_prompts[key]

    async def run(
        self,
        user_message: str,
        conversation_history: list[dict[str, str]] | None = None,
        language: str = "en",
        conversation_id: str | None = None,
        image_data: str | None = None,
        image_kind: str | None = None,
    ) -> AsyncGenerator[AgentEvent, None]:
        """
        Run one turn of the agent loop.

        Parameters
        ----------
        user_message : str
            The patient's latest message.
        conversation_history : list or None
            Previous messages in the conversation.
        language : str
            "ar" or "en".
        conversation_id : str or None
            Real conversation UUID from the database (injected into tool args).
        image_data : str or None
            Optional base64 data URI of an attached medical image. When present,
            forces a call to `analyze_vision` before normal LLM iteration.
        image_kind : str or None
            Optional hint about image type (xray | ct | photo | skin | wound | other).

        Yields
        ------
        AgentEvent
            Streaming events for the frontend.
        """
        # ── Step 0: PII scrub + branch auto-detect ──
        safe_message = scrub_pii(user_message)
        self._resolve_branch(safe_message)

        # ── Step 0.5: Force analyze_vision when image is attached ──
        # نُدخل تحليل الصورة مباشرةً قبل ما الـ LLM يقرر، لأن أغلب موديلات
        # الـ chat-only ما بتشوفش الصور، فبنحقن نتيجة analyze_vision كـ tool message.
        vision_tool_result: dict[str, Any] | None = None
        if image_data:
            vision_tool = self.registry.get("analyze_vision")
            if vision_tool:
                yield AgentEvent(
                    type="tool_start",
                    content="Analyzing image...",
                    data={"tool": "analyze_vision"},
                )
                try:
                    tool_input = vision_tool.input_schema(
                        image_url=image_data,
                        image_kind=image_kind or "other",
                        context=safe_message[:1500],
                        language=language,
                        conversation_id=conversation_id or "",
                    )
                    vision_tool_result = await vision_tool.run(tool_input)
                except Exception as e:
                    vision_tool_result = {
                        "findings": [],
                        "urgency": "routine",
                        "confidence": 0.0,
                        "is_medical": True,
                        "error": str(e),
                    }
                yield AgentEvent(
                    type="tool_result",
                    data={"tool": "analyze_vision", "result": vision_tool_result},
                )

        # ── Step 1: Red-flag fast path (base + branch-specific) ──
        # red_flag_result = self.red_flag_detector.detect(safe_message)
        # ── Step 1: Red-flag fast path (AI Semantic Triage) ──
        # نستخدم دالة الذكاء الاصطناعي وبنمررلها رسالة المريض والـ llm
        red_flag_result = await self.red_flag_detector.detect_with_ai(safe_message, self.llm)

        # Delegate to standalone branch tools for richer checks
        if self._pediatric_ctx:
            _apply_pediatric_red_flags(self._pediatric_ctx, safe_message, red_flag_result)

        if self._pregnancy_ctx or self.patient_is_pregnant:
            _apply_pregnancy_red_flags(safe_message, red_flag_result)

        if red_flag_result["has_red_flag"] and red_flag_result["severity"] == "emergency":
            try:
                from app.core.metrics import red_flags_detected_total, triage_level_total

                branch = (
                    "pediatric"
                    if self._pediatric_ctx
                    else ("pregnancy" if self._pregnancy_ctx else "base")
                )
                red_flags_detected_total.labels("emergency", branch).inc()
                triage_level_total.labels("emergency").inc()
            except Exception:
                pass
            yield AgentEvent(
                type="red_flag",
                data=red_flag_result,
                content="Emergency red flag detected — seek immediate medical attention.",
            )
            yield AgentEvent(
                type="triage",
                data={
                    "level": "emergency",
                    "score": 100,
                    "reasoning": "Emergency red flag detected",
                },
            )
            yield AgentEvent(type="done")
            return

        # ── Step 2: Build messages ──
        system_prompt = self._load_system_prompt(language)
        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

        if conversation_history:
            messages.extend(conversation_history)

        # لو في صورة، نضيف ملاحظة للرسالة عشان حتى الموديلات النصية البحتة
        # (زي Llama 3.x / Allam) تعرف إن المستخدم بعت صورة وإن نتيجة التحليل
        # هتبقى في tool message اللي بعد كده.
        user_content = safe_message
        if vision_tool_result is not None:
            attach_note = (
                "\n\n[المستخدم أرفق صورة طبية للتحليل — راجع نتيجة أداة analyze_vision]"
                if language == "ar"
                else "\n\n[The user attached a medical image — see the analyze_vision tool result below]"
            )
            user_content = f"{safe_message}{attach_note}"
        messages.append({"role": "user", "content": user_content})

        # ── Inject vision tool result as conversation context ──
        # بعد ما رسالة المستخدم النصية اتحطّت، بنضيف رسالة assistant وبعدها tool
        # علشان الـ LLM يلاقي تحليل الصورة كأنه استخدم الأداة بنفسه.
        if vision_tool_result is not None:
            vision_call_id = "call_vision_pre"
            messages.append(
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": vision_call_id,
                            "type": "function",
                            "function": {
                                "name": "analyze_vision",
                                "arguments": json.dumps(
                                    {"image_kind": image_kind or "other", "language": language}
                                ),
                            },
                        }
                    ],
                }
            )
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": vision_call_id,
                    "content": json.dumps(vision_tool_result, ensure_ascii=False),
                }
            )

        # ── Step 2: ReAct loop ──
        tools = self.registry.to_openai_schema() if self.registry.list_all() else None

        for iteration in range(MAX_ITERATIONS):
            accumulated = ""
            tool_calls = []

            async for event in self.llm.generate_stream(
                messages=messages,
                tools=tools,
                max_tokens=768,
                temperature=0.3,
            ):
                if event["type"] == "token":
                    accumulated += event["content"]

                elif event["type"] == "tool_call":
                    tool_calls.append(event)

                elif event["type"] == "error":
                    yield AgentEvent(
                        type="error",
                        content=event.get("content", "LLM API error"),
                        data=event,
                    )
                    yield AgentEvent(type="done")
                    return

                elif event["type"] == "done":
                    break

            # If the LLM called tools — the preceding text is "thinking"
            # Send it as a separate thinking event (not shown in main message)
            if tool_calls and accumulated:
                yield AgentEvent(
                    type="thinking",
                    content=accumulated,
                    data={"iteration": iteration},
                )

            # If the LLM produced a final answer (no tools), stream it as normal tokens
            if not tool_calls and accumulated:
                # Stream the final response character by character for the frontend animation
                for chunk in accumulated:
                    yield AgentEvent(type="token", content=chunk)

            # If the LLM called a tool
            if tool_calls:
                for tc in tool_calls:
                    tool_name = tc.get("name", "")
                    tool = self.registry.get(tool_name)

                    if not tool:
                        yield AgentEvent(
                            type="error",
                            content=f"Unknown tool: {tool_name}",
                        )
                        continue

                    # Parse tool arguments
                    try:
                        args_str = tc.get("args", "{}")
                        args_dict = json.loads(args_str) if isinstance(args_str, str) else args_str

                        # Inject real conversation_id for tools that need it
                        if conversation_id and tool_name in (
                            "summarize_for_doctor",
                            "format_soap",
                        ):
                            args_dict["conversation_id"] = conversation_id

                        # Validate with pydantic
                        input_obj = tool.input_schema(**args_dict)
                    except Exception as e:
                        yield AgentEvent(
                            type="error",
                            content=f"Tool args error: {e}",
                        )
                        continue

                    yield AgentEvent(
                        type="tool_start",
                        content=f"Running {tool_name}...",
                        data={"tool": tool_name},
                    )

                    # Execute tool
                    from time import perf_counter as _pc

                    _tool_start = _pc()
                    try:
                        result = await tool.run(input_obj)
                        _tool_outcome = "success"
                    except Exception as e:
                        result = {"error": str(e)}
                        _tool_outcome = "error"
                    finally:
                        try:
                            from app.core.metrics import (
                                tool_calls_total,
                                tool_duration_seconds,
                            )

                            tool_calls_total.labels(tool_name, _tool_outcome).inc()
                            tool_duration_seconds.labels(tool_name).observe(
                                _pc() - _tool_start
                            )
                        except Exception:
                            pass

                    yield AgentEvent(
                        type="tool_result",
                        data={"tool": tool_name, "result": result},
                    )

                    # Emit triage event from score_triage result
                    if tool_name == "score_triage" and "level" in result:
                        yield AgentEvent(
                            type="triage",
                            data=result,
                        )

                    # Feed tool result back to LLM
                    messages.append(
                        {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": f"call_{iteration}",
                                    "type": "function",
                                    "function": {
                                        "name": tool_name,
                                        "arguments": json.dumps(args_dict),
                                    },
                                }
                            ],
                        }
                    )
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": f"call_{iteration}",
                            "content": json.dumps(result),
                        }
                    )

                    # ── Tree-of-Thought trigger ──
                    # لو أداة score_triage رجّعت urgent، نشوف لو محتاجين ToT
                    if tool_name == "score_triage" and result.get("level") == "urgent":
                        tot_tool = self.registry.get("tot_differential_diagnosis")
                        if tot_tool:
                            try:
                                symptoms, history = ToTOrchestrator.build_tot_context(
                                    messages, self.patient_age, self.patient_conditions
                                )
                                # نجمع المصادر من الرسايل (زي ما بنعمل في safety gate)
                                tot_sources = self._extract_sources(messages)
                                tot_input = tot_tool.input_schema(
                                    symptoms=symptoms,
                                    history=history,
                                    sources=tot_sources,
                                    language=language,
                                )
                                tot_result = await tot_tool.run(tot_input)

                                yield AgentEvent(
                                    type="tot_branches",
                                    data=ToTOrchestrator.format_branches_for_ui(tot_result),
                                )

                                # نغذي نتيجة ToT للـ LLM عشان ياخدها في الاعتبار
                                messages.append(
                                    {
                                        "role": "assistant",
                                        "content": None,
                                        "tool_calls": [
                                            {
                                                "id": f"call_{iteration}_tot",
                                                "type": "function",
                                                "function": {
                                                    "name": "tot_differential_diagnosis",
                                                    "arguments": json.dumps(
                                                        {"symptoms": symptoms, "language": language}
                                                    ),
                                                },
                                            }
                                        ],
                                    }
                                )
                                messages.append(
                                    {
                                        "role": "tool",
                                        "tool_call_id": f"call_{iteration}_tot",
                                        "content": json.dumps(tot_result),
                                    }
                                )
                            except Exception:
                                pass  # فشل ToT — نكمل ReAct عادي
            else:
                # LLM responded without tool calls — reply is complete
                if accumulated:
                    # Yield triage event if score_triage result is detected in messages
                    for msg in reversed(messages):
                        if msg["role"] == "tool" and "level" in msg.get("content", ""):
                            try:
                                triage_data = json.loads(msg["content"])
                                if "level" in triage_data:
                                    yield AgentEvent(
                                        type="triage",
                                        data=triage_data,
                                    )
                            except json.JSONDecodeError:
                                pass
                            break
                break

        # ── Fallback: if tools completed but no text response ──
        if not accumulated and any(msg["role"] == "tool" for msg in messages):
            # Ask the LLM one final time to produce a text summary
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "لقد أكملت التحليل باستخدام الأدوات. "
                        "الآن قم بكتابة رد مختصر ومفيد للمريض باللغة العربية يلخص النتائج والتوصيات."
                        if language == "ar"
                        else "You have completed the analysis using tools. "
                        "Now write a brief, helpful response to the patient summarizing the findings and recommendations."
                    ),
                }
            )
            try:
                async for event in self.llm.generate_stream(
                    messages=messages,
                    tools=None,  # No more tool calls allowed
                    max_tokens=512,
                    temperature=0.3,
                ):
                    if event["type"] == "token":
                        accumulated += event["content"]
                        yield AgentEvent(type="token", content=event["content"])
                    elif event["type"] == "done":
                        break
            except Exception:
                pass

        # ── Post-LLM Safety Gate (Stage 3) ──
        # بعد ما الـ Agent يخلص رده، بنمرره على بوابة الأمان
        # اللي بتدقق كل claim طبي مقابل المصادر اللي رجعها الـ RAG
        if self._safety_gate and accumulated:
            retrieved_sources = self._extract_sources(messages)
            gate_result = await self._safety_gate.check(
                assistant_text=accumulated,
                sources=retrieved_sources,
            )
            yield AgentEvent(
                type="safety",
                data={
                    "action": gate_result.action,
                    "original_text": gate_result.original_text,
                    "safe_text": gate_result.safe_text,
                    "assessment": gate_result.assessment,
                },
            )

            # لو الرد اتعدل، نبعت النص الآمن بدل الأصلي
            # (لكن التوكينز الأصلية Already اتبعتت streaming —
            #  بنضيف تصحيح هنا)
            if gate_result.action in ("rewrite", "flag"):
                yield AgentEvent(
                    type="token",
                    content="\n\n---\n⚠️ "
                    + gate_result.safe_text[len(gate_result.original_text) :].lstrip(),
                )

        yield AgentEvent(type="done")

    # ── Helper: استخراج المصادر من رسايل الـ Agent ──

    @staticmethod
    def _extract_sources(messages: list[dict]) -> list[dict[str, str]]:
        """
        يستخرج المصادر الطبية اللي رجعها الـ RAG من رسايل الأدوات.

        بيدور في messages على tool_result بتاع retrieve_medical_knowledge
        وبياخد الـ chunks اللي رجعت — كل chunk فيه title + content_excerpt.
        """
        sources: list[dict[str, str]] = []
        for msg in messages:
            if msg.get("role") != "tool":
                continue
            try:
                data = json.loads(msg.get("content", "{}"))
            except json.JSONDecodeError:
                continue
            # ناخد chunks من نتيجة retrieve_medical_knowledge
            for chunk in data.get("chunks", []):
                sources.append(
                    {
                        "title": chunk.get("title", chunk.get("source", "")),
                        "content": chunk.get("content_excerpt", chunk.get("content", "")),
                    }
                )
        return sources


# ── Branch red-flag helpers (called from agent.run fast-path) ──


def _apply_pediatric_red_flags(
    ctx: "PediatricContext",
    text: str,
    result: dict,
) -> None:
    """Augment red_flag_result with pediatric-specific rules."""
    from app.ai.tools.assess_pediatric_safety import PEDIATRIC_RED_FLAGS

    text_lower = text.lower()
    for rule in PEDIATRIC_RED_FLAGS:
        if rule["age_max_months"] is not None and ctx.age_months >= rule["age_max_months"]:
            continue
        matched = [kw for kw in rule["flags"] if kw.lower() in text_lower]
        if matched:
            result["has_red_flag"] = True
            if rule["level"] == "emergency":
                result["severity"] = "emergency"
            result["flags"].append(
                {
                    "keyword": matched[0],
                    "language": "rule",
                    "level": rule["level"],
                    "branch": "pediatric",
                    "reason": rule["reason"],
                }
            )


def _apply_pregnancy_red_flags(text: str, result: dict) -> None:
    """Augment red_flag_result with OB red-flag rules."""
    from app.ai.tools.assess_pregnancy_safety import OB_RED_FLAGS

    text_lower = text.lower()
    for rule in OB_RED_FLAGS:
        all_keywords = rule["keywords_en"] + rule["keywords_ar"]
        matched = [kw for kw in all_keywords if kw.lower() in text_lower]
        if matched:
            result["has_red_flag"] = True
            if rule["level"] == "emergency":
                result["severity"] = "emergency"
            result["flags"].append(
                {
                    "keyword": matched[0],
                    "language": "rule",
                    "level": rule["level"],
                    "branch": "pregnancy",
                    "condition": rule["condition"],
                }
            )
