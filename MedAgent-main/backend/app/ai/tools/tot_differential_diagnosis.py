"""
أداة tot_differential_diagnosis — تشخيص تفريقي متعدد الفروع (Tree-of-Thought)

لما الأعراض تكون ambiguous (مش واضحة) والـ triage urgent، الأداة دي بتولّد
3 فروع تشخيصية (hypotheses)، ترجع لكل فرع supporting evidence من الـ RAG،
وتختار أفضل 2 فيهم للعرض على المريض.

دا الـ ToT mode من §8.8.2 في الخطة.
"""

import json
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.ai.agent.base import Tool

MAX_TOT_BRANCHES = 3  # الحد الأقصى للفروع
MAX_TOT_DEPTH = 2  # أقصى عمق للتفكير


# ── Input / Output Schemas ──


class ToTInput(BaseModel):
    """
    مدخلات أداة التشخيص التفريقي.

    symptoms: الأعراض اللي قالها المريض (نص وصفي)
    history: التاريخ المرضي — عمر، أمراض مزمنة، أدوية، حساسية
    sources: المصادر الطبية من RAG
    language: "ar" أو "en"
    """

    symptoms: str = Field(..., min_length=1, description="وصف الأعراض من المريض")
    history: str = Field(default="", description="العمر، الأمراض المزمنة، الأدوية")
    sources: list[dict[str, str]] = Field(
        default_factory=list,
        description="المصادر الطبية المسترجعة من RAG",
    )
    language: str = Field(default="en", pattern="^(ar|en)$")


# ── ToT Engine ──


class ToTDifferentialEngine:
    """
    محرك التشخيص التفريقي — بيولّد فروع تشخيصية ويسجلها.

    بيشتغل على 3 مراحل:
    1. Branch generation — يطلب من LLM يطلع 3 hypotheses
    2. Branch scoring — يرجع لكل فرع المصادر اللي بتدعمه
    3. Pruning — يختار أفضل 2 فروع ويعرضهم
    """

    _prompt_path: Path | None = None

    def __init__(self, llm_provider):
        """
        llm_provider: أي instance من LLMProvider
        """
        self._llm = llm_provider

        # نحمل الـ prompt مرة واحدة
        if ToTDifferentialEngine._prompt_path is None:
            ToTDifferentialEngine._prompt_path = (
                Path(__file__).resolve().parent.parent / "prompts" / "tot_differential_en.txt"
            )

    async def generate_branches(
        self,
        symptoms: str,
        history: str,
        sources: list[dict],
    ) -> dict[str, Any]:
        """
        يولّد الفروع التشخيصية باستخدام LLM.

        1. يبني الـ prompt بالمدخلات
        2. يبعت لـ LLM (non-streaming)
        3. يفسر الـ JSON الراجع
        4. يختار أفضل 2 (pruning)
        """

        # 1. نبني الـ prompt
        prompt_template = ToTDifferentialEngine._prompt_path.read_text("utf-8")
        sources_text = self._format_sources(sources)

        prompt = prompt_template.format(
            symptoms=symptoms,
            history=history or "No significant history reported",
            sources=sources_text
            or "(No medical sources available — use general clinical knowledge)",
        )

        # 2. نبعت لـ LLM
        messages = [{"role": "user", "content": prompt}]
        result = await self._llm.generate(
            messages=messages,
            tools=None,
            max_tokens=1024,
            temperature=0.4,  # شوية إبداع عشان الفروع تكون متنوعة
        )

        raw_content = result.get("content", "")

        # 3. نفسر الـ JSON
        tot_result = self._parse_json(raw_content)
        branches = tot_result.get("branches", [])

        # 4. Pruning — نخلي أفضل 2 (أو 3 لو قليلين)
        if len(branches) > 2:
            # نرتبهم حسب probability (الأعلى أولاً)
            branches.sort(key=lambda b: b.get("probability", 0), reverse=True)
            branches = branches[:2]

        return {
            "branches": branches,
            "mode": "tree_of_thought",
            "total_branches_generated": len(branches),
        }

    @staticmethod
    def _format_sources(sources: list[dict]) -> str:
        """ينسق المصادر لنص مقروء للـ LLM."""
        if not sources:
            return ""

        lines = []
        for i, src in enumerate(sources):
            title = src.get("title", src.get("source", f"Source {i}"))
            content = src.get("content", src.get("content_excerpt", ""))
            if len(content) > 400:
                content = content[:400] + "..."
            lines.append(f"[{i}] {title}")
            lines.append(f"    {content}")
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _parse_json(raw: str) -> dict[str, Any]:
        """يستخرج JSON من رد الـ LLM (مع تعامل مع markdown fences)."""
        try:
            return json.loads(raw.strip())
        except json.JSONDecodeError:
            pass

        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        return {"branches": [], "_raw": raw[:200], "_parse_error": True}


# ── Tool ──


class ToTDifferentialDiagnosisTool(Tool):
    """
    الأداة المسجلة في ToolRegistry — تشخيص تفريقي متعدد الفروع.

    الـ Agent بيستخدمها لما يكتشف إن الأعراض ambiguous ومحتاجة تحليل أعمق.
    """

    def __init__(self, llm_provider):
        self._engine = ToTDifferentialEngine(llm_provider)

    @property
    def name(self) -> str:
        return "tot_differential_diagnosis"

    @property
    def description(self) -> str:
        return (
            "Generate multiple diagnostic hypotheses (Tree-of-Thought branching) for "
            "ambiguous symptom presentations. Returns 2-3 ranked branches with "
            "probability scores, supporting evidence, and recommended actions. "
            "Use when symptoms are unclear and multiple distinct conditions could explain them."
        )

    @property
    def input_schema(self) -> type[BaseModel]:
        return ToTInput

    async def run(self, input_data: BaseModel) -> dict[str, Any]:
        if not isinstance(input_data, ToTInput):
            raise TypeError(f"Expected ToTInput, got {type(input_data)}")

        return await self._engine.generate_branches(
            symptoms=input_data.symptoms,
            history=input_data.history,
            sources=input_data.sources,
        )
