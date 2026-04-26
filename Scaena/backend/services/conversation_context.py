from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend import models
from backend.services.conversation_visibility import visible_conversation_messages


def _compact_text(value: str | None, limit: int = 220) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def conversation_messages_payload(db: Session, conv: models.Conversation) -> list[dict]:
    return [
        {
            "direction": msg.direction,
            "body": msg.body,
            "subject": msg.subject,
            "created_at": msg.created_at.isoformat() if msg.created_at else "",
        }
        for msg in visible_conversation_messages(db, conv)
    ]


def prior_venue_context(
    db: Session,
    entertainer_id: str,
    venue_name: str | None,
    contact_email: str | None = None,
    exclude_conversation_id: str | None = None,
    exclude_pitch_id: str | None = None,
    limit_conversations: int = 3,
    limit_messages_per_conversation: int = 4,
) -> str:
    """Summarize previous conversations with the same venue/company.

    This is intentionally separate from the active thread memory. Old dates and rates
    are relationship context, not current commitments unless the current thread repeats them.
    """
    clean_venue = str(venue_name or "").strip()
    clean_email = str(contact_email or "").strip().lower()
    if not clean_venue and not clean_email:
        return ""

    convs_by_venue = (
        db.query(models.Conversation)
        .filter(models.Conversation.entertainer_id == entertainer_id)
        .filter(func.lower(models.Conversation.venue_name) == clean_venue.lower())
        .order_by(models.Conversation.updated_at.desc(), models.Conversation.created_at.desc())
        .all()
    ) if clean_venue else []

    convs_by_email: list[models.Conversation] = []
    if clean_email:
        pitch_ids = [
            row[0]
            for row in (
                db.query(models.Pitch.id)
                .filter(models.Pitch.entertainer_id == entertainer_id)
                .filter(func.lower(models.Pitch.recipient_email) == clean_email)
                .all()
            )
        ]
        if pitch_ids:
            convs_by_email = (
                db.query(models.Conversation)
                .filter(models.Conversation.entertainer_id == entertainer_id)
                .filter(models.Conversation.pitch_id.in_(pitch_ids))
                .order_by(models.Conversation.updated_at.desc(), models.Conversation.created_at.desc())
                .all()
            )

    seen: set[str] = set()
    convs: list[models.Conversation] = []
    for conv in [*convs_by_venue, *convs_by_email]:
        if conv.id in seen:
            continue
        seen.add(conv.id)
        convs.append(conv)

    lines: list[str] = []
    included = 0
    for conv in convs:
        if exclude_conversation_id and conv.id == exclude_conversation_id:
            continue
        if exclude_pitch_id and conv.pitch_id == exclude_pitch_id:
            continue

        pitch = db.query(models.Pitch).filter(models.Pitch.id == conv.pitch_id).first() if conv.pitch_id else None
        booking = None
        if pitch:
            booking = db.query(models.Booking).filter(models.Booking.pitch_id == pitch.id).first()

        status_bits = []
        if pitch and pitch.status:
            status_bits.append(f"pitch status {pitch.status}")
        if pitch and pitch.response_type:
            status_bits.append(f"response {pitch.response_type}")
        if booking:
            if booking.conversation_stage:
                status_bits.append(f"booking stage {booking.conversation_stage}")
            if booking.agreed_rate:
                status_bits.append(f"rate ${booking.agreed_rate:.0f}")
            if booking.show_date:
                status_bits.append(f"date {booking.show_date}")

        header = f"Prior {conv.venue_name or clean_venue or clean_email} thread"
        if status_bits:
            header += f" ({'; '.join(status_bits)})"
        lines.append(f"- {header}.")

        messages = visible_conversation_messages(db, conv)[-limit_messages_per_conversation:]
        for msg in messages:
            speaker = "Recipient" if msg.direction == "inbound" else "Sender"
            when = msg.created_at.strftime("%Y-%m-%d") if msg.created_at else "unknown date"
            lines.append(f"  {speaker} on {when}: {_compact_text(msg.body)}")

        included += 1
        if included >= limit_conversations:
            break

    return "\n".join(lines)[:2400]
