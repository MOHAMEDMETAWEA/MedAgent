"""Handoff service — generate, send, review doctor summaries."""

import uuid
from datetime import UTC, date, datetime, time

from sqlalchemy import func, or_, select

from app.common.audit import log_action
from app.core.database import get_session
from app.models.conversation import Conversation
from app.models.handoff_summary import HandoffSummary
from app.models.messages import Message
from app.models.users import User

_TRIAGE_PRIORITY = {"emergency": 100, "urgent": 70, "routine": 30}

# Allowed transitions for the handoff status state machine.
_STATUS_TRANSITIONS = {
    "new": {"acknowledged", "in_progress", "reviewed", "closed"},
    "acknowledged": {"in_progress", "reviewed", "closed"},
    "in_progress": {"reviewed", "closed"},
    "reviewed": {"closed"},
    "closed": set(),
}

_VALID_SORTS = {"priority", "sent_at", "created_at"}


async def generate_handoff(
    conversation_id: uuid.UUID,
    patient_user_id: uuid.UUID,
) -> HandoffSummary:
    """Generate a handoff summary from a conversation."""
    async with get_session() as session:
        result = await session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )
        messages = result.scalars().all()

        conv = await session.get(Conversation, conversation_id)

        summary = _build_summary_markdown(conv, messages)

        priority = _TRIAGE_PRIORITY.get(conv.triage_level, 0) if conv else 0
        target_language = conv.language if conv else None

        handoff = HandoffSummary(
            conversation_id=conversation_id,
            patient_user_id=patient_user_id,
            summary_markdown=summary,
            status="new",
            priority=priority,
            target_language=target_language,
        )
        session.add(handoff)

        if conv:
            conv.status = "completed"
            conv.completed_at = datetime.now(UTC)

        await session.commit()
        await session.refresh(handoff)

        log_action(
            "generate_handoff",
            user_id=patient_user_id,
            resource_type="handoff_summary",
            resource_id=handoff.id,
        )

        return handoff


async def get_handoff(handoff_id: uuid.UUID, user_id: uuid.UUID) -> HandoffSummary | None:
    """Get a handoff by ID. Allows patient owner OR assigned doctor."""
    async with get_session() as session:
        result = await session.execute(
            select(HandoffSummary).where(
                HandoffSummary.id == handoff_id,
                or_(
                    HandoffSummary.patient_user_id == user_id,
                    HandoffSummary.doctor_user_id == user_id,
                ),
            )
        )
        return result.scalar_one_or_none()


async def list_patient_handoffs(
    user_id: uuid.UUID, page: int = 1, page_size: int = 20
) -> tuple[list[HandoffSummary], int]:
    """List handoffs for a patient."""
    async with get_session() as session:
        query = (
            select(HandoffSummary)
            .where(HandoffSummary.patient_user_id == user_id)
            .order_by(HandoffSummary.created_at.desc())
        )
        count_query = (
            select(func.count())
            .select_from(HandoffSummary)
            .where(HandoffSummary.patient_user_id == user_id)
        )

        total = (await session.execute(count_query)).scalar() or 0
        result = await session.execute(query.offset((page - 1) * page_size).limit(page_size))
        return list(result.scalars().all()), total


async def list_doctor_inbox(
    doctor_user_id: uuid.UUID,
    *,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    triage_level: str | None = None,
    language: str | None = None,
    q: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    sort: str = "priority",
) -> tuple[list[HandoffSummary], int]:
    """List handoffs received by a doctor with filters."""
    sort = sort if sort in _VALID_SORTS else "priority"

    async with get_session() as session:
        needs_conv_join = triage_level is not None or language is not None
        needs_user_join = bool(q)

        query = select(HandoffSummary).where(HandoffSummary.doctor_user_id == doctor_user_id)
        count_query = (
            select(func.count(HandoffSummary.id))
            .select_from(HandoffSummary)
            .where(HandoffSummary.doctor_user_id == doctor_user_id)
        )

        if needs_conv_join:
            query = query.join(Conversation, Conversation.id == HandoffSummary.conversation_id)
            count_query = count_query.join(
                Conversation, Conversation.id == HandoffSummary.conversation_id
            )
        if needs_user_join:
            query = query.join(User, User.id == HandoffSummary.patient_user_id)
            count_query = count_query.join(User, User.id == HandoffSummary.patient_user_id)

        if status:
            query = query.where(HandoffSummary.status == status)
            count_query = count_query.where(HandoffSummary.status == status)
        if triage_level:
            query = query.where(Conversation.triage_level == triage_level)
            count_query = count_query.where(Conversation.triage_level == triage_level)
        if language:
            query = query.where(Conversation.language == language)
            count_query = count_query.where(Conversation.language == language)
        if q:
            pattern = f"%{q}%"
            search_clause = or_(
                User.full_name.ilike(pattern),
                HandoffSummary.summary_markdown.ilike(pattern),
            )
            query = query.where(search_clause)
            count_query = count_query.where(search_clause)
        if from_date:
            start = datetime.combine(from_date, time.min, tzinfo=UTC)
            query = query.where(HandoffSummary.created_at >= start)
            count_query = count_query.where(HandoffSummary.created_at >= start)
        if to_date:
            end = datetime.combine(to_date, time.max, tzinfo=UTC)
            query = query.where(HandoffSummary.created_at <= end)
            count_query = count_query.where(HandoffSummary.created_at <= end)

        if sort == "priority":
            query = query.order_by(
                HandoffSummary.priority.desc(),
                HandoffSummary.sent_at.desc().nulls_last(),
            )
        elif sort == "sent_at":
            query = query.order_by(HandoffSummary.sent_at.desc().nulls_last())
        else:
            query = query.order_by(HandoffSummary.created_at.desc())

        total = (await session.execute(count_query)).scalar() or 0
        result = await session.execute(query.offset((page - 1) * page_size).limit(page_size))
        return list(result.scalars().all()), total


async def count_inbox_by_status(doctor_user_id: uuid.UUID) -> dict[str, int]:
    """Return per-status counts for a doctor's inbox."""
    async with get_session() as session:
        result = await session.execute(
            select(HandoffSummary.status, func.count(HandoffSummary.id))
            .where(HandoffSummary.doctor_user_id == doctor_user_id)
            .group_by(HandoffSummary.status)
        )
        counts = {"new": 0, "acknowledged": 0, "in_progress": 0, "reviewed": 0, "closed": 0}
        total = 0
        for row_status, count in result.all():
            if row_status in counts:
                counts[row_status] = count
            total += count
        counts["total"] = total
        return counts


async def send_to_doctor(
    handoff_id: uuid.UUID,
    doctor_user_id: uuid.UUID,
) -> bool:
    """Send a handoff to a specific doctor."""
    async with get_session() as session:
        handoff = await session.get(HandoffSummary, handoff_id)
        if not handoff:
            return False

        handoff.doctor_user_id = doctor_user_id
        handoff.sent_at = datetime.now(UTC)
        if handoff.status == "closed":
            return False
        handoff.status = "new"
        await session.commit()

        log_action("send_handoff", resource_type="handoff_summary", resource_id=handoff_id)
        return True


async def review_handoff(
    handoff_id: uuid.UUID,
    doctor_user_id: uuid.UUID,
    notes: str | None = None,
) -> bool:
    """Mark handoff as reviewed by doctor."""
    async with get_session() as session:
        handoff = await session.get(HandoffSummary, handoff_id)
        if not handoff or handoff.doctor_user_id != doctor_user_id:
            return False

        now = datetime.now(UTC)
        handoff.reviewed_at = now
        if handoff.status not in {"reviewed", "closed"}:
            handoff.status = "reviewed"
        if notes:
            handoff.doctor_private_notes = notes
        await session.commit()

        log_action(
            "review_handoff",
            user_id=doctor_user_id,
            resource_type="handoff_summary",
            resource_id=handoff_id,
        )
        return True


async def update_handoff_status(
    handoff_id: uuid.UUID,
    doctor_user_id: uuid.UUID,
    new_status: str,
    notes: str | None = None,
) -> tuple[bool, str | None]:
    """Advance a handoff through the status workflow.

    Returns (success, error_code). Error codes: not_found, invalid_transition.
    """
    async with get_session() as session:
        handoff = await session.get(HandoffSummary, handoff_id)
        if not handoff or handoff.doctor_user_id != doctor_user_id:
            return False, "not_found"

        current = handoff.status or "new"
        if new_status not in _STATUS_TRANSITIONS.get(current, set()):
            return False, "invalid_transition"

        now = datetime.now(UTC)
        handoff.status = new_status
        if new_status in {"acknowledged", "in_progress"} and handoff.acknowledged_at is None:
            handoff.acknowledged_at = now
        elif new_status == "reviewed" and handoff.reviewed_at is None:
            handoff.reviewed_at = now
        elif new_status == "closed" and handoff.closed_at is None:
            handoff.closed_at = now
            if handoff.reviewed_at is None:
                handoff.reviewed_at = now

        if notes:
            handoff.doctor_private_notes = notes

        await session.commit()

        log_action(
            f"handoff_status_{new_status}",
            user_id=doctor_user_id,
            resource_type="handoff_summary",
            resource_id=handoff_id,
        )
        return True, None


def _build_summary_markdown(conv: Conversation | None, messages: list[Message]) -> str:
    """Build structured handoff summary from conversation."""

    patient_msgs = [m for m in messages if m.role == "user"]
    assistant_msgs = [m for m in messages if m.role == "assistant"]

    lines = []
    lines.append("# Doctor Handoff Summary")
    lines.append("")
    lines.append(f"**Date:** {datetime.now(UTC).strftime('%Y-%m-%d %H:%M')} UTC")
    lines.append("")

    # Triage
    if conv and conv.triage_level:
        lines.append(f"## Triage: {conv.triage_level.upper()}")
        if conv.triage_score:
            lines.append(f"Score: {conv.triage_score}/100")
        lines.append("")

    # Chief complaint
    lines.append("## Chief Complaint")
    if patient_msgs:
        lines.append(patient_msgs[0].text[:500])
    lines.append("")

    # # Patient messages
    # lines.append("## Patient History")
    # for msg in patient_msgs[1:]:
    #     lines.append(f"- {msg.text[:200]}")
    # lines.append("")

    # # AI Assessment
    # lines.append("## AI Assessment")
    # for msg in assistant_msgs:
    #     lines.append(msg.text[:500])
    #     lines.append("")
    # lines.append("")
# -------------
    # Medical Interview (Q&A)
    lines.append("## Patient History (Interview)")
        
    # هندمج كل سؤال من الـ AI مع الإجابة اللي بعده من المريض
    # assistant_msgs فيها الأسئلة
    # patient_msgs[1:] فيها الإجابات (لأن أول رسالة كانت الشكوى الأساسية)
    for ai_msg, pt_msg in zip(assistant_msgs, patient_msgs[1:]):
        lines.append(f"**Doctor (AI):** {ai_msg.text}")
        lines.append(f"**Patient:** {pt_msg.text}")
        lines.append("")
    
    # AI Assessment (ممكن نسيب التقييم المبدئي الأخير لو موجود)
    lines.append("## AI Assessment")
    if assistant_msgs:
        # ناخد آخر رسالة بس من الـ AI اللي غالباً بيكون فيها التقييم النهائي
        lines.append(assistant_msgs[-1].text)
# -------------------
    # Red flags
    if conv and conv.red_flags_detected:
        lines.append("## Red Flags Detected")
        for flag in conv.red_flags_detected:
            if isinstance(flag, dict):
                lines.append(f"- {flag.get('keyword', flag)}")
            else:
                lines.append(f"- {flag}")
        lines.append("")

    # Disclaimer
    lines.append("---")
    lines.append("")
    lines.append(
        "**Disclaimer:** This summary is AI-generated and is for informational "
        "purposes only. It does NOT constitute a medical diagnosis or replace "
        "professional medical judgment. Always consult a licensed physician."
    )

    return "\n".join(lines)
