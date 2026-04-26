from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend import models, schemas
from typing import List
from datetime import datetime

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.get("/active", response_model=List[schemas.BookingOut])
def active_bookings(db: Session = Depends(get_db)):
    return (
        db.query(models.Booking)
        .filter(models.Booking.conversation_stage.in_(["confirmed", "logistics", "pre_show", "post_show"]))
        .all()
    )


@router.get("/completed-unrebooked", response_model=List[schemas.BookingOut])
def completed_unrebooked(db: Session = Depends(get_db)):
    return (
        db.query(models.Booking)
        .filter(
            models.Booking.conversation_stage == "post_show",
            models.Booking.rebooking_sent == False,
        )
        .all()
    )


@router.post("/create")
def create_booking(pitch_id: str, db: Session = Depends(get_db)):
    pitch = db.query(models.Pitch).filter(models.Pitch.id == pitch_id).first()
    if not pitch:
        raise HTTPException(status_code=404, detail="Pitch not found")
    conv = db.query(models.Conversation).filter(models.Conversation.pitch_id == pitch_id).first()
    booking = models.Booking(
        entertainer_id=pitch.entertainer_id,
        pitch_id=pitch_id,
        target_id=conv.id if conv else pitch_id,
        venue_name=pitch.venue_name,
        agreed_rate=pitch.negotiated_price or pitch.proposed_rate,
        original_pitch_id=pitch_id,
        conversation_stage="confirmed",
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return {"booking_id": booking.id}


@router.post("/conversation-message")
def save_booking_message(data: schemas.BookingMessageCreate, db: Session = Depends(get_db)):
    msg = models.BookingMessage(**data.model_dump())
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return {"message_id": msg.id}


@router.patch("/conversation-message/{message_id}")
def mark_booking_message_sent(message_id: str, db: Session = Depends(get_db)):
    msg = db.query(models.BookingMessage).filter(models.BookingMessage.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    msg.status = "sent"
    msg.sent_at = datetime.utcnow()
    # Advance booking stage
    stage_order = ["confirmed", "logistics", "pre_show", "post_show", "rebooking"]
    booking = db.query(models.Booking).filter(models.Booking.id == msg.booking_id).first()
    if booking and msg.stage in stage_order:
        idx = stage_order.index(msg.stage)
        if idx + 1 < len(stage_order):
            booking.conversation_stage = stage_order[idx + 1]
    db.commit()
    return {"ok": True}


@router.get("/messages/{booking_id}", response_model=List[schemas.BookingMessageOut])
def get_booking_messages(booking_id: str, db: Session = Depends(get_db)):
    return (
        db.query(models.BookingMessage)
        .filter(models.BookingMessage.booking_id == booking_id)
        .order_by(models.BookingMessage.created_at)
        .all()
    )
