"""Handoff router — doctor summary endpoints."""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import select

from app.core.deps import get_current_user, require_role
from app.modules.handoff.schemas import (
    HandoffCreate,
    HandoffListResponse,
    HandoffResponse,
    HandoffReview,
    HandoffSend,
    HandoffStatusUpdate,
    InboxCountResponse,
)
from app.modules.handoff.service import (
    count_inbox_by_status,
    generate_handoff,
    get_handoff,
    list_doctor_inbox,
    list_patient_handoffs,
    review_handoff,
    send_to_doctor,
    update_handoff_status,
)

handoff_router = APIRouter(prefix="/handoffs", tags=["handoffs"])


@handoff_router.post("", response_model=HandoffResponse, status_code=201)
async def create_handoff(
    body: HandoffCreate,
    current_user: dict = Depends(get_current_user),
):
    """Generate a handoff summary from a conversation."""
    user_id = uuid.UUID(current_user["sub"])
    handoff = await generate_handoff(body.conversation_id, user_id)
    if not handoff:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return _to_response(handoff)


@handoff_router.get("", response_model=HandoffListResponse)
async def list_my_handoffs(
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_user),
):
    """List handoffs for the current patient."""
    user_id = uuid.UUID(current_user["sub"])
    items, total = await list_patient_handoffs(user_id, page, page_size)
    return HandoffListResponse(
        items=[_to_response(h) for h in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@handoff_router.get("/{handoff_id}", response_model=HandoffResponse)
async def view_handoff(
    handoff_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
):
    """View a handoff summary."""
    user_id = uuid.UUID(current_user["sub"])
    handoff = await get_handoff(handoff_id, user_id)
    if not handoff:
        raise HTTPException(status_code=404, detail="Handoff not found")
    return _to_response(handoff)


@handoff_router.get("/{handoff_id}/pdf")
async def download_pdf(
    handoff_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
):
    """Download handoff as PDF.

    When weasyprint or its native dependencies (Pango/Cairo) aren't available,
    fall back to a printable HTML page so the browser can save it as PDF.
    """
    user_id = uuid.UUID(current_user["sub"])
    handoff = await get_handoff(handoff_id, user_id)
    if not handoff:
        raise HTTPException(status_code=404, detail="Handoff not found")

    from app.common.pdf import generate_pdf, markdown_to_html

    # title = handoff.title or "MedAgent Handoff Summary"
    title = f"MedAgent Handoff - ID: {str(handoff.id)[:8]}" or handoff.title
    html = markdown_to_html(handoff.summary_markdown, title=title)

    try:
        pdf_bytes = await generate_pdf(html)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="handoff_{handoff_id}.pdf"'},
        )
    except (ImportError, OSError) as e:
        # Native PDF rendering unavailable — return a print-ready HTML page.
        printable_html = html.replace(
            "</body>",
            "<script>window.addEventListener('load',()=>setTimeout(()=>window.print(),200));</script></body>",
            1,
        )
        return Response(
            content=printable_html.encode("utf-8"),
            media_type="text/html; charset=utf-8",
            headers={
                "Content-Disposition": f'inline; filename="handoff_{handoff_id}.html"',
                "X-PDF-Generation": "unavailable",
                "X-PDF-Error": str(e)[:200],
            },
        )


@handoff_router.get("/{handoff_id}/export")
async def export_handoff(
    handoff_id: uuid.UUID,
    format: str = "fhir",
    current_user: dict = Depends(get_current_user),
):
    """Export a handoff in interoperable formats (FHIR R4 Bundle or HL7 v2.5)."""
    user_id = uuid.UUID(current_user["sub"])
    handoff = await get_handoff(handoff_id, user_id)
    if not handoff:
        raise HTTPException(status_code=404, detail="Handoff not found")

    from app.core.database import get_session
    from app.models.conversation import Conversation
    from app.models.handoff_exports import HandoffExport
    from app.models.users import User

    async with get_session() as session:
        conv = await session.get(Conversation, handoff.conversation_id)
        patient = await session.get(User, handoff.patient_user_id)

    fmt = format.lower()
    if fmt == "fhir":
        from app.modules.handoff.fhir_export import build_fhir_bundle, serialize_bundle

        bundle = build_fhir_bundle(handoff, conv, patient)
        body = serialize_bundle(bundle)
        media_type = "application/fhir+json"
        filename = f"handoff_{handoff_id}.fhir.json"
    elif fmt == "hl7":
        from app.modules.handoff.hl7_export import build_hl7_v2

        body = build_hl7_v2(handoff, conv, patient)
        media_type = "application/hl7-v2"
        filename = f"handoff_{handoff_id}.hl7"
    else:
        raise HTTPException(status_code=400, detail="format must be 'fhir' or 'hl7'")

    # Best-effort: persist export record (idempotent on (handoff_id, format))
    try:
        async with get_session() as session:
            existing = await session.execute(
                select(HandoffExport).where(
                    HandoffExport.handoff_id == handoff_id,
                    HandoffExport.format == fmt,
                )
            )
            row = existing.scalar_one_or_none()
            if row is None:
                row = HandoffExport(
                    handoff_id=handoff_id,
                    format=fmt,
                    content_inline=body,
                    bytes=len(body.encode("utf-8")),
                )
                session.add(row)
            else:
                row.content_inline = body
                row.bytes = len(body.encode("utf-8"))
            await session.commit()
    except Exception:
        # Persistence failure should not block the download
        pass

    return Response(
        content=body.encode("utf-8"),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@handoff_router.post("/{handoff_id}/send")
async def send_handoff(
    handoff_id: uuid.UUID,
    body: HandoffSend,
    current_user: dict = Depends(get_current_user),
):
    """Send handoff to a doctor."""
    success = await send_to_doctor(handoff_id, body.doctor_user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Handoff not found")
    return {"sent": True}


@handoff_router.post("/{handoff_id}/review")
async def review_handoff_endpoint(
    handoff_id: uuid.UUID,
    body: HandoffReview,
    current_user: dict = Depends(require_role("doctor", "admin")),
):
    """Doctor reviews a received handoff."""
    doctor_id = uuid.UUID(current_user["sub"])
    success = await review_handoff(handoff_id, doctor_id, body.notes)
    if not success:
        raise HTTPException(status_code=404, detail="Handoff not found")
    return {"reviewed": True}


# ── Doctor inbox ──


@handoff_router.get("/doctor/inbox", response_model=HandoffListResponse)
async def doctor_inbox(
    page: int = 1,
    page_size: int = 20,
    status: str | None = Query(
        default=None, pattern="^(new|acknowledged|in_progress|reviewed|closed)$"
    ),
    triage_level: str | None = Query(default=None, pattern="^(emergency|urgent|routine)$"),
    language: str | None = Query(default=None, max_length=5),
    q: str | None = Query(default=None, max_length=200),
    from_date: date | None = None,
    to_date: date | None = None,
    sort: str = Query(default="priority", pattern="^(priority|sent_at|created_at)$"),
    current_user: dict = Depends(require_role("doctor")),
):
    """List handoffs received by the current doctor."""
    doctor_id = uuid.UUID(current_user["sub"])
    items, total = await list_doctor_inbox(
        doctor_id,
        page=page,
        page_size=page_size,
        status=status,
        triage_level=triage_level,
        language=language,
        q=q,
        from_date=from_date,
        to_date=to_date,
        sort=sort,
    )
    return HandoffListResponse(
        items=[_to_response(h) for h in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@handoff_router.get("/doctor/inbox/count", response_model=InboxCountResponse)
async def doctor_inbox_count(
    current_user: dict = Depends(require_role("doctor")),
):
    """Per-status counts for the doctor's inbox (used for tab badges)."""
    doctor_id = uuid.UUID(current_user["sub"])
    counts = await count_inbox_by_status(doctor_id)
    return InboxCountResponse(**counts)


@handoff_router.patch("/{handoff_id}/status")
async def patch_handoff_status(
    handoff_id: uuid.UUID,
    body: HandoffStatusUpdate,
    current_user: dict = Depends(require_role("doctor", "admin")),
):
    """Advance a handoff through the doctor workflow state machine."""
    doctor_id = uuid.UUID(current_user["sub"])
    success, error = await update_handoff_status(handoff_id, doctor_id, body.status, body.notes)
    if not success:
        if error == "invalid_transition":
            raise HTTPException(status_code=409, detail="Invalid status transition")
        raise HTTPException(status_code=404, detail="Handoff not found")
    return {"status": body.status}


def _to_response(h) -> HandoffResponse:
    return HandoffResponse(
        id=h.id,
        conversation_id=h.conversation_id,
        patient_user_id=h.patient_user_id,
        doctor_user_id=h.doctor_user_id,
        status=h.status or "new",
        priority=h.priority or 0,
        target_specialty=h.target_specialty,
        target_language=h.target_language,
        auto_routed=bool(h.auto_routed),
        sent_at=h.sent_at,
        acknowledged_at=h.acknowledged_at,
        reviewed_at=h.reviewed_at,
        closed_at=h.closed_at,
        doctor_private_notes=h.doctor_private_notes,
        summary_markdown=h.summary_markdown,
        pdf_url=None,
        created_at=h.created_at,
        updated_at=h.updated_at,
    )
