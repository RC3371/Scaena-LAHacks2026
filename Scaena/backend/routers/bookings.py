from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend import models, schemas
from backend.services.booking_pipeline import checklist_json, default_logistics_checklist, ensure_booking_for_pitch
from backend.services.pitch_generation import remove_long_dashes
from typing import List
from datetime import datetime, timedelta
import json

router = APIRouter(prefix="/bookings", tags=["bookings"])

STAGE_ALIASES = {
    "confirmed": "secured",
    "logistics": "logistics_pending",
    "pre_show": "show_scheduled",
    "post_show": "rebook_ready",
    "rebooking": "rebook_outreach_sent",
}

ACTIVE_STAGES = {"secured", "logistics_pending", "show_scheduled", "post_show_followup", "confirmed", "logistics", "pre_show"}
REBOOK_READY_STAGES = {"rebook_ready", "post_show"}


def _normalize_stage(stage: str | None) -> str:
    raw = (stage or "secured").strip()
    return STAGE_ALIASES.get(raw, raw)


def _parse_checklist(raw: str | None) -> dict:
    checklist = default_logistics_checklist()
    if raw:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                checklist.update({k: bool(v) for k, v in parsed.items() if k in checklist})
        except Exception:
            pass
    return checklist


def _parse_show_date(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return None


def _days_until_show(booking: models.Booking) -> int | None:
    show = _parse_show_date(booking.show_date)
    if not show:
        return None
    return (show.date() - datetime.utcnow().date()).days


def _pipeline_reminders(booking: models.Booking, checklist: dict) -> list[dict]:
    reminders = []
    stage = _normalize_stage(booking.conversation_stage)
    missing = [key for key, done in checklist.items() if not done]
    days = _days_until_show(booking)

    if stage in {"secured", "logistics_pending"} and missing:
        top_missing = ", ".join(key.replace("_", " ") for key in missing[:3])
        reminders.append({
            "level": "urgent" if "date_confirmed" in missing or "payment_confirmed" in missing else "todo",
            "text": f"Confirm logistics: {top_missing}.",
        })
    if days is not None and days <= 3 and days >= 0 and stage in {"secured", "logistics_pending", "show_scheduled"}:
        reminders.append({"level": "urgent", "text": "Show is within 3 days. Confirm arrival, set length, and promo assets."})
    if days is not None and days < 0 and stage != "rebook_ready" and not booking.performance_completed_at:
        reminders.append({"level": "urgent", "text": "Performance date has passed. Add post-show notes and resolve the performance."})
    if stage == "rebook_ready" and not booking.rebooking_sent:
        reminders.append({"level": "ready", "text": "Ready for Agent 2 rebook outreach."})
    if booking.rebooking_sent or stage == "rebook_outreach_sent":
        reminders.append({"level": "done", "text": "Rebook outreach has been created in Outreach."})

    return reminders or [{"level": "ok", "text": "Pipeline is on track."}]


def _pipeline_health(booking: models.Booking, checklist: dict) -> str:
    stage = _normalize_stage(booking.conversation_stage)
    days = _days_until_show(booking)
    if stage == "rebook_outreach_sent" or booking.rebooking_sent:
        return "rebook sent"
    if stage == "rebook_ready":
        return "ready to rebook"
    if days is not None and days < 0:
        return "needs post-show notes"
    if any(not checklist[key] for key in ("date_confirmed", "rate_confirmed", "load_in_confirmed", "payment_confirmed")):
        return "needs logistics"
    if days is not None and days <= 3:
        return "at risk"
    return "on track"


def _next_action(booking: models.Booking, checklist: dict) -> str:
    health = _pipeline_health(booking, checklist)
    if health == "needs logistics":
        return "Confirm date, load-in, payment, and set details."
    if health == "needs post-show notes":
        return "Resolve the performance and capture crowd/payment notes."
    if health == "ready to rebook":
        return "Send this relationship back to Outreach for a rebook ask."
    if health == "at risk":
        return "Send a final pre-show logistics confirmation."
    if health == "rebook sent":
        return "Watch Outreach for the rebook conversation."
    return "Keep monitoring the show timeline."


def _booking_payload(booking: models.Booking) -> dict:
    checklist = _parse_checklist(booking.logistics_checklist)
    stage = _normalize_stage(booking.conversation_stage)
    return {
        "id": booking.id,
        "entertainer_id": booking.entertainer_id,
        "pitch_id": booking.pitch_id,
        "target_id": booking.target_id,
        "venue_name": booking.venue_name,
        "agreed_rate": booking.agreed_rate,
        "show_date": booking.show_date,
        "conversation_stage": stage,
        "logistics_checklist": checklist,
        "show_summary": booking.show_summary,
        "post_show_notes": booking.post_show_notes,
        "crowd_size": booking.crowd_size,
        "audience_reaction": booking.audience_reaction,
        "payout_received": bool(booking.payout_received),
        "venue_satisfaction": booking.venue_satisfaction,
        "rebook_recommended": booking.rebook_recommended,
        "next_reminder_at": booking.next_reminder_at,
        "performance_completed_at": booking.performance_completed_at,
        "rebooking_sent": bool(booking.rebooking_sent),
        "pipeline_health": _pipeline_health(booking, checklist),
        "pipeline_reminders": _pipeline_reminders(booking, checklist),
        "next_action": _next_action(booking, checklist),
        "days_until_show": _days_until_show(booking),
        "created_at": booking.created_at,
        "updated_at": booking.updated_at,
    }


@router.get("/active")
def active_bookings(db: Session = Depends(get_db)):
    bookings = (
        db.query(models.Booking)
        .filter(models.Booking.conversation_stage.in_(list(ACTIVE_STAGES)))
        .order_by(models.Booking.created_at.desc())
        .all()
    )
    return [_booking_payload(booking) for booking in bookings]


@router.get("/completed-unrebooked")
def completed_unrebooked(db: Session = Depends(get_db)):
    bookings = (
        db.query(models.Booking)
        .filter(
            models.Booking.conversation_stage.in_(list(REBOOK_READY_STAGES)),
            models.Booking.rebooking_sent == False,
        )
        .order_by(models.Booking.created_at.desc())
        .all()
    )
    return [_booking_payload(booking) for booking in bookings]


@router.post("/create")
def create_booking(pitch_id: str, db: Session = Depends(get_db)):
    pitch = db.query(models.Pitch).filter(models.Pitch.id == pitch_id).first()
    if not pitch:
        raise HTTPException(status_code=404, detail="Pitch not found")
    conv = db.query(models.Conversation).filter(models.Conversation.pitch_id == pitch_id).first()
    booking, created = ensure_booking_for_pitch(db, pitch, conv)
    return {"booking_id": booking.id, "created": created}


@router.patch("/{booking_id}/pipeline")
def update_pipeline(
    booking_id: str,
    data: schemas.BookingPipelineUpdate,
    db: Session = Depends(get_db),
):
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    update = data.model_dump(exclude_unset=True)
    if "conversation_stage" in update and update["conversation_stage"]:
        booking.conversation_stage = _normalize_stage(update["conversation_stage"])
    if "agreed_rate" in update:
        booking.agreed_rate = update["agreed_rate"]
    if "show_date" in update:
        booking.show_date = update["show_date"]
    if "show_summary" in update:
        booking.show_summary = update["show_summary"]
    if "post_show_notes" in update:
        booking.post_show_notes = update["post_show_notes"]
    if "crowd_size" in update:
        booking.crowd_size = update["crowd_size"]
    if "audience_reaction" in update:
        booking.audience_reaction = update["audience_reaction"]
    if "payout_received" in update:
        booking.payout_received = update["payout_received"]
    if "venue_satisfaction" in update:
        booking.venue_satisfaction = update["venue_satisfaction"]
    if "rebook_recommended" in update:
        booking.rebook_recommended = update["rebook_recommended"]
    if "next_reminder_at" in update:
        booking.next_reminder_at = update["next_reminder_at"]
    if "logistics_checklist" in update and update["logistics_checklist"] is not None:
        current = _parse_checklist(booking.logistics_checklist)
        current.update({k: bool(v) for k, v in update["logistics_checklist"].items() if k in current})
        if booking.show_date:
            current["date_confirmed"] = True
        if booking.agreed_rate:
            current["rate_confirmed"] = True
        booking.logistics_checklist = checklist_json(current)

    checklist = _parse_checklist(booking.logistics_checklist)
    if booking.show_date and checklist and not checklist.get("date_confirmed"):
        checklist["date_confirmed"] = True
        booking.logistics_checklist = checklist_json(checklist)
    if booking.agreed_rate and checklist and not checklist.get("rate_confirmed"):
        checklist["rate_confirmed"] = True
        booking.logistics_checklist = checklist_json(checklist)

    booking.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(booking)
    return _booking_payload(booking)


@router.patch("/{booking_id}/resolve-performance")
def resolve_performance(
    booking_id: str,
    data: schemas.PerformanceResolve | None = None,
    db: Session = Depends(get_db),
):
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    payload = data.model_dump(exclude_none=True) if data else {}
    booking.conversation_stage = "rebook_ready" if payload.get("rebook_recommended", booking.rebook_recommended if booking.rebook_recommended is not None else True) else "post_show_followup"
    booking.performance_completed_at = datetime.utcnow()
    booking.post_show_notes = payload.get("post_show_notes", booking.post_show_notes)
    booking.crowd_size = payload.get("crowd_size", booking.crowd_size)
    booking.audience_reaction = payload.get("audience_reaction", booking.audience_reaction)
    booking.payout_received = payload.get("payout_received", booking.payout_received)
    booking.venue_satisfaction = payload.get("venue_satisfaction", booking.venue_satisfaction)
    booking.rebook_recommended = payload.get("rebook_recommended", booking.rebook_recommended if booking.rebook_recommended is not None else True)
    booking.next_reminder_at = datetime.utcnow() + timedelta(days=7)
    summary = (booking.show_summary or "").strip()
    marker = "Performance resolved; ready for rebook outreach." if booking.conversation_stage == "rebook_ready" else "Performance resolved; post-show follow-up needed before rebook."
    if marker not in summary:
        booking.show_summary = f"{summary}; {marker}" if summary else marker
    booking.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(booking)
    return _booking_payload(booking)


@router.post("/conversation-message")
def save_booking_message(data: schemas.BookingMessageCreate, db: Session = Depends(get_db)):
    payload = data.model_dump()
    payload["subject"] = remove_long_dashes(payload.get("subject"))
    payload["body"] = remove_long_dashes(payload.get("body"))
    msg = models.BookingMessage(**payload)
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
    stage_order = ["secured", "logistics_pending", "show_scheduled", "post_show_followup", "rebook_ready", "rebook_outreach_sent"]
    booking = db.query(models.Booking).filter(models.Booking.id == msg.booking_id).first()
    normalized_msg_stage = _normalize_stage(msg.stage)
    if booking and normalized_msg_stage in stage_order:
        idx = stage_order.index(normalized_msg_stage)
        if idx + 1 < len(stage_order):
            booking.conversation_stage = stage_order[idx + 1]
            booking.updated_at = datetime.utcnow()
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
