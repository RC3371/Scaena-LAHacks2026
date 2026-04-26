from sqlalchemy.orm import Session

from backend import models


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
        conversation_stage="confirmed",
    )
    pitch.status = "booked"
    pitch.response_type = "accepted"
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking, True
