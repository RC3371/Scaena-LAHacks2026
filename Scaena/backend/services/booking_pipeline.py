from sqlalchemy.orm import Session
import json

from backend import models


DEFAULT_LOGISTICS_CHECKLIST = {
    "date_confirmed": False,
    "rate_confirmed": False,
    "contact_confirmed": False,
    "set_length_confirmed": False,
    "load_in_confirmed": False,
    "payment_confirmed": False,
    "promo_assets_sent": False,
    "contract_invoice_sent": False,
}


def default_logistics_checklist() -> dict[str, bool]:
    return dict(DEFAULT_LOGISTICS_CHECKLIST)


def checklist_json(checklist: dict | None = None) -> str:
    merged = default_logistics_checklist()
    if checklist:
        merged.update({k: bool(v) for k, v in checklist.items() if k in merged})
    return json.dumps(merged)


def ensure_booking_for_pitch(
    db: Session,
    pitch: models.Pitch,
    conv: models.Conversation | None = None,
) -> tuple[models.Booking, bool]:
    """Create or refresh the secured deal that belongs to an accepted pitch."""
    existing = db.query(models.Booking).filter(models.Booking.pitch_id == pitch.id).first()
    if existing:
        pitch.status = "booked"
        pitch.response_type = "accepted"
        if not existing.logistics_checklist:
            existing.logistics_checklist = checklist_json({
                "rate_confirmed": bool(existing.agreed_rate),
                "date_confirmed": bool(existing.show_date),
                "contact_confirmed": True,
            })
        db.commit()
        db.refresh(existing)
        return existing, False

    if conv is None:
        conv = db.query(models.Conversation).filter(models.Conversation.pitch_id == pitch.id).first()

    booking = models.Booking(
        entertainer_id=pitch.entertainer_id,
        pitch_id=pitch.id,
        target_id=conv.id if conv else pitch.id,
        venue_name=(conv.venue_name if conv else None) or pitch.venue_name,
        agreed_rate=pitch.negotiated_price or pitch.proposed_rate,
        original_pitch_id=pitch.id,
        conversation_stage="secured",
        logistics_checklist=checklist_json({
            "rate_confirmed": bool(pitch.negotiated_price or pitch.proposed_rate),
            "contact_confirmed": bool(pitch.recipient_email),
        }),
    )
    pitch.status = "booked"
    pitch.response_type = "accepted"
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking, True
