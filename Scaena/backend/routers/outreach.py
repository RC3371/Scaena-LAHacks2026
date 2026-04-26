from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from backend.database import get_db
from backend import models, schemas
from backend.services.conversation_context import prior_venue_context
from backend.services.mongo_store import mirror_pitch_sent, mirror_venues
from backend.websocket_manager import manager
from backend.services.booking_pipeline import ensure_booking_for_pitch
from backend.services.pitch_generation import generate_pitch_for_venue, generate_rebook_pitch, remove_long_dashes
from typing import List, Optional
from datetime import datetime, timedelta
import asyncio
import json

try:
    from agents.research_sources import curated_opportunity_fallback, discover_live_venues, live_sources_configured
except Exception:
    curated_opportunity_fallback = None
    discover_live_venues = None
    live_sources_configured = lambda: False

router = APIRouter(prefix="/outreach", tags=["outreach"])


def _save_pitch_with_conversation(db: Session, payload: dict) -> models.Pitch:
    payload = {**payload}
    payload["pitch_subject"] = remove_long_dashes(payload.get("pitch_subject"))
    payload["pitch_body"] = remove_long_dashes(payload.get("pitch_body"))
    pitch = models.Pitch(**payload)
    if payload.get("status") == "sent":
        pitch.sent_at = datetime.utcnow()
    db.add(pitch)
    db.flush()

    conv = models.Conversation(
        entertainer_id=payload["entertainer_id"],
        pitch_id=pitch.id,
        venue_name=payload.get("venue_name"),
    )
    db.add(conv)
    db.flush()

    if payload.get("status") in {"sent", "responded", "booked"}:
        msg = models.ConversationMessage(
            conversation_id=conv.id,
            direction="outbound",
            message_type="initial_pitch",
            subject=payload.get("pitch_subject"),
            body=payload.get("pitch_body"),
        )
        db.add(msg)
    db.commit()
    db.refresh(pitch)
    return pitch


def _entertainer_payload(entertainer: models.Entertainer) -> dict:
    return {
        "id": entertainer.id,
        "name": entertainer.name,
        "type": entertainer.type,
        "genre": entertainer.genre,
        "location": entertainer.location,
        "experience_years": entertainer.experience_years,
        "social_followers": entertainer.social_followers,
        "highlights": entertainer.highlights,
        "current_rate": entertainer.current_rate,
    }


def _venue_payload(venue: models.Venue | None, pitch: models.Pitch | None = None, data: schemas.PitchGenerateCreate | None = None) -> dict:
    return {
        "name": (venue.name if venue else None) or (pitch.venue_name if pitch else None) or (data.venue_name if data else None),
        "contact_name": (venue.contact_name if venue else None),
        "venue_type": (venue.venue_type if venue else None) or (data.venue_type if data else None),
        "contact_email": (venue.contact_email if venue else None) or (pitch.recipient_email if pitch else None) or (data.recipient_email if data else None),
        "contact_approach": (venue.contact_approach if venue else None) or (pitch.venue_contact_approach if pitch else None) or (data.venue_contact_approach if data else None),
        "why_fits": (venue.why_fits if venue else None) or (data.why_fits if data else None),
        "source_url": (venue.source_url if venue else None) or (data.source_url if data else None),
        "specific_examples": (venue.specific_examples if venue else None) or (data.specific_examples if data else None),
    }


@router.post("/pitch")
def save_pitch(data: schemas.PitchCreate, db: Session = Depends(get_db)):
    pitch = _save_pitch_with_conversation(db, data.model_dump())
    return {"pitch_id": pitch.id}


@router.post("/pitch/generated")
async def generate_and_save_pitch(data: schemas.PitchGenerateCreate, db: Session = Depends(get_db)):
    entertainer = db.query(models.Entertainer).filter(models.Entertainer.id == data.entertainer_id).first()
    if not entertainer:
        raise HTTPException(status_code=404, detail="Entertainer not found")

    venue = None
    if data.venue_id:
        venue = (
            db.query(models.Venue)
            .filter(models.Venue.id == data.venue_id, models.Venue.entertainer_id == data.entertainer_id)
            .first()
        )
        if not venue:
            raise HTTPException(status_code=404, detail="Venue not found")

    venue_payload = _venue_payload(venue, data=data)
    if not venue_payload.get("name"):
        raise HTTPException(status_code=400, detail="venue_id or venue_name is required")

    entertainer_payload = _entertainer_payload(entertainer)
    rate = data.proposed_rate or entertainer.current_rate or 350
    generated = generate_pitch_for_venue(entertainer_payload, venue_payload, rate)

    pitch = _save_pitch_with_conversation(db, {
        "entertainer_id": data.entertainer_id,
        "venue_id": venue.id if venue else None,
        "venue_name": venue_payload["name"],
        "entertainer_type": entertainer.type,
        "recipient_email": venue_payload.get("contact_email"),
        "venue_contact_approach": venue_payload.get("contact_approach"),
        "pitch_subject": generated["subject"],
        "pitch_body": generated["body"],
        "proposed_rate": rate,
        "status": data.status,
    })

    await manager.broadcast({
        "agent_id": "agent2",
        "event_type": "pitch_ready",
        "entertainer_id": data.entertainer_id,
        "message": f"Generated {generated.get('generation_source', 'fallback').upper()} pitch for {venue_payload['name']}.",
        "target": venue_payload["name"],
        "pitch_id": pitch.id,
        "status": data.status,
    })
    return {
        "pitch_id": pitch.id,
        "generation_source": generated.get("generation_source"),
        "pitch_subject": generated["subject"],
        "pitch_body": generated["body"],
    }


@router.post("/pitch/rebook")
async def generate_and_save_rebook_pitch(data: schemas.RebookPitchCreate, db: Session = Depends(get_db)):
    booking = (
        db.query(models.Booking)
        .filter(models.Booking.id == data.booking_id)
        .filter(models.Booking.entertainer_id == data.entertainer_id)
        .first()
    )
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    entertainer = db.query(models.Entertainer).filter(models.Entertainer.id == data.entertainer_id).first()
    if not entertainer:
        raise HTTPException(status_code=404, detail="Entertainer not found")

    original_pitch = None
    if booking.pitch_id:
        original_pitch = db.query(models.Pitch).filter(models.Pitch.id == booking.pitch_id).first()
    if not original_pitch and booking.original_pitch_id:
        original_pitch = db.query(models.Pitch).filter(models.Pitch.id == booking.original_pitch_id).first()

    venue = None
    if original_pitch and original_pitch.venue_id:
        venue = db.query(models.Venue).filter(models.Venue.id == original_pitch.venue_id).first()
    if not venue and booking.venue_name:
        venue = (
            db.query(models.Venue)
            .filter(models.Venue.entertainer_id == data.entertainer_id)
            .filter(models.Venue.name == booking.venue_name)
            .order_by(models.Venue.created_at.desc())
            .first()
        )

    rate = booking.agreed_rate or (original_pitch.proposed_rate if original_pitch else None) or entertainer.current_rate or 350
    generated = generate_rebook_pitch(
        _entertainer_payload(entertainer),
        {
            "id": booking.id,
            "venue_name": booking.venue_name,
            "agreed_rate": booking.agreed_rate,
            "show_summary": booking.show_summary,
            "conversation_stage": booking.conversation_stage,
        },
        rate,
        prior_context=prior_venue_context(
            db,
            data.entertainer_id,
            booking.venue_name,
            contact_email=(
                (original_pitch.recipient_email if original_pitch else None)
                or (venue.contact_email if venue else None)
            ),
        ),
    )

    pitch = _save_pitch_with_conversation(db, {
        "entertainer_id": data.entertainer_id,
        "venue_id": venue.id if venue else (original_pitch.venue_id if original_pitch else None),
        "batch_id": f"rebook-{booking.id}",
        "venue_name": booking.venue_name,
        "entertainer_type": entertainer.type,
        "recipient_email": (
            (original_pitch.recipient_email if original_pitch else None)
            or (venue.contact_email if venue else None)
        ),
        "venue_contact_approach": "Rebook from prior successful show",
        "pitch_subject": generated["subject"],
        "pitch_body": generated["body"],
        "proposed_rate": rate,
        "strategy_note": "Agent 2 rebook directive: ask whether the venue wants to book another show, not an initial booking.",
        "status": data.status,
    })

    booking.rebooking_sent = True
    booking.conversation_stage = "rebook_outreach_sent"
    db.commit()

    await manager.broadcast({
        "agent_id": "agent2",
        "event_type": "pitch_ready",
        "entertainer_id": data.entertainer_id,
        "message": f"Generated rebook outreach for {booking.venue_name}.",
        "target": booking.venue_name,
        "pitch_id": pitch.id,
        "booking_id": booking.id,
        "status": data.status,
        "generation_source": generated.get("generation_source"),
    })
    return {
        "pitch_id": pitch.id,
        "booking_id": booking.id,
        "generation_source": generated.get("generation_source"),
        "pitch_subject": generated["subject"],
        "pitch_body": generated["body"],
    }


@router.post("/pitch/{pitch_id}/regenerate")
async def regenerate_pitch(pitch_id: str, data: schemas.PitchRegenerateRequest, db: Session = Depends(get_db)):
    pitch = db.query(models.Pitch).filter(models.Pitch.id == pitch_id).first()
    if not pitch:
        raise HTTPException(status_code=404, detail="Pitch not found")

    entertainer_id = data.entertainer_id or pitch.entertainer_id
    entertainer = db.query(models.Entertainer).filter(models.Entertainer.id == entertainer_id).first()
    if not entertainer:
        raise HTTPException(status_code=404, detail="Entertainer not found")

    venue = None
    if pitch.venue_id:
        venue = db.query(models.Venue).filter(models.Venue.id == pitch.venue_id).first()
    if not venue and pitch.venue_name:
        venue = (
            db.query(models.Venue)
            .filter(models.Venue.entertainer_id == entertainer_id, models.Venue.name == pitch.venue_name)
            .first()
        )

    venue_payload = _venue_payload(venue, pitch=pitch)
    generated = generate_pitch_for_venue(
        _entertainer_payload(entertainer),
        venue_payload,
        pitch.proposed_rate or entertainer.current_rate or 350,
        strategy_instruction=data.strategy_instruction,
    )

    pitch.pitch_subject = generated["subject"]
    pitch.pitch_body = generated["body"]
    pitch.strategy_note = data.strategy_instruction
    db.commit()
    db.refresh(pitch)

    await manager.broadcast({
        "agent_id": "agent2",
        "event_type": "pitch_ready",
        "entertainer_id": entertainer_id,
        "message": f"Regenerated {generated.get('generation_source', 'fallback').upper()} pitch for {pitch.venue_name}.",
        "target": pitch.venue_name,
        "pitch_id": pitch.id,
        "status": pitch.status,
    })
    return {
        "pitch_id": pitch.id,
        "generation_source": generated.get("generation_source"),
        "pitch_subject": pitch.pitch_subject,
        "pitch_body": pitch.pitch_body,
    }


@router.get("/pitches/{entertainer_id}", response_model=List[schemas.PitchOut])
def list_pitches(entertainer_id: str, status: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(models.Pitch).filter(models.Pitch.entertainer_id == entertainer_id)
    if status:
        q = q.filter(models.Pitch.status == status)
    return q.order_by(models.Pitch.created_at.desc()).all()


@router.get("/pitch-by-target/{target_id}")
def get_pitch_by_target(target_id: str, db: Session = Depends(get_db)):
    conv = db.query(models.Conversation).filter(models.Conversation.id == target_id).first()
    pitch = None
    if conv:
        pitch = db.query(models.Pitch).filter(models.Pitch.id == conv.pitch_id).first()
    if not pitch:
        pitch = db.query(models.Pitch).filter(models.Pitch.id == target_id).first()
    if not pitch:
        raise HTTPException(status_code=404, detail="Pitch not found")
    return {
        "id": pitch.id,
        "venue_name": pitch.venue_name,
        "pitch_subject": pitch.pitch_subject,
        "pitch_body": pitch.pitch_body,
        "entertainer_type": pitch.entertainer_type,
    }


@router.patch("/pitch/{pitch_id}")
def update_pitch(pitch_id: str, data: schemas.PitchUpdate, db: Session = Depends(get_db)):
    pitch = db.query(models.Pitch).filter(models.Pitch.id == pitch_id).first()
    if not pitch:
        raise HTTPException(status_code=404, detail="Pitch not found")
    update = data.model_dump(exclude_none=True)
    if "status" in update and update["status"] == "sent" and not pitch.sent_at:
        pitch.sent_at = datetime.utcnow()
        # Create booking if accepted
    if "response_type" in update and update["response_type"] == "accepted":
        update["status"] = "responded"
    if "pitch_subject" in update:
        update["pitch_subject"] = remove_long_dashes(update["pitch_subject"])
    if "pitch_body" in update:
        update["pitch_body"] = remove_long_dashes(update["pitch_body"])
    for k, v in update.items():
        setattr(pitch, k, v)
    db.commit()
    if pitch.response_type == "accepted":
        conv = db.query(models.Conversation).filter(models.Conversation.pitch_id == pitch.id).first()
        ensure_booking_for_pitch(db, pitch, conv)
    if update.get("status") == "sent":
        mirror_pitch_sent(pitch, recipient=pitch.recipient_email, dry_run=False, source="outreach_status_update")
    return {"ok": True}


@router.get("/pending-followup")
def pending_followup(db: Session = Depends(get_db)):
    cutoff = datetime.utcnow() - timedelta(days=3)
    pitches = db.query(models.Pitch).filter(
        and_(
            models.Pitch.status == "sent",
            models.Pitch.response_type.is_(None),
            models.Pitch.sent_at <= cutoff,
        )
    ).all()
    return [
        {
            "pitch_id": p.id,
            "entertainer_id": p.entertainer_id,
            "venue_name": p.venue_name,
            "entertainer_type": p.entertainer_type,
            "pitch_subject": p.pitch_subject,
            "followup_count": p.followup_count,
        }
        for p in pitches
    ]


@router.get("/rejected-or-later")
def rejected_or_later(db: Session = Depends(get_db)):
    cutoff = datetime.utcnow() - timedelta(days=60)
    pitches = db.query(models.Pitch).filter(
        and_(
            models.Pitch.response_type.in_(["rejected", "maybe"]),
            models.Pitch.created_at <= cutoff,
        )
    ).all()
    return [
        {
            "pitch_id": p.id,
            "entertainer_id": p.entertainer_id,
            "venue_name": p.venue_name,
            "entertainer_type": p.entertainer_type,
        }
        for p in pitches
    ]


@router.post("/batch")
def save_batch(data: schemas.BatchCreate, db: Session = Depends(get_db)):
    batch = models.OutreachBatch(**data.model_dump())
    db.add(batch)
    db.commit()
    return {"ok": True}


@router.post("/followup")
def save_followup(data: schemas.FollowUpCreate, db: Session = Depends(get_db)):
    payload = data.model_dump()
    payload["subject"] = remove_long_dashes(payload.get("subject"))
    payload["body"] = remove_long_dashes(payload.get("body"))
    fu = models.FollowUp(**payload)
    db.add(fu)
    # Increment pitch followup_count
    pitch = db.query(models.Pitch).filter(models.Pitch.id == data.pitch_id).first()
    if pitch:
        pitch.followup_count = (pitch.followup_count or 0) + 1
    db.commit()
    db.refresh(fu)
    return {"followup_id": fu.id}


@router.patch("/followup/{followup_id}")
def mark_followup_sent(followup_id: str, db: Session = Depends(get_db)):
    fu = db.query(models.FollowUp).filter(models.FollowUp.id == followup_id).first()
    if not fu:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    fu.status = "sent"
    fu.sent_at = datetime.utcnow()
    conv = db.query(models.Conversation).filter(models.Conversation.pitch_id == fu.pitch_id).first()
    if conv:
        message_type = f"followup_{fu.followup_number}"
        msg = (
            db.query(models.ConversationMessage)
            .filter(models.ConversationMessage.conversation_id == conv.id)
            .filter(models.ConversationMessage.direction == "outbound")
            .filter(models.ConversationMessage.message_type == message_type)
            .order_by(models.ConversationMessage.created_at.desc())
            .first()
        )
        if msg:
            msg.subject = fu.subject
            msg.body = fu.body
            msg.created_at = fu.sent_at
        else:
            db.add(models.ConversationMessage(
                conversation_id=conv.id,
                direction="outbound",
                message_type=message_type,
                subject=fu.subject,
                body=fu.body,
                created_at=fu.sent_at,
            ))
    db.commit()
    return {"ok": True}


@router.post("/followup-result")
def log_followup_result(data: schemas.FollowUpResultCreate, db: Session = Depends(get_db)):
    result = models.FollowUpResult(**data.model_dump())
    db.add(result)
    db.commit()
    return {"ok": True}


@router.post("/reengagement")
def save_reengagement(data: schemas.ReengagementCreate, db: Session = Depends(get_db)):
    payload = data.model_dump()
    payload["subject"] = remove_long_dashes(payload.get("subject"))
    payload["body"] = remove_long_dashes(payload.get("body"))
    re = models.Reengagement(**payload)
    db.add(re)
    db.commit()
    db.refresh(re)
    return {"reengagement_id": re.id}


@router.post("/research-refinement")
async def research_refinement(data: schemas.ResearchRefinementRequest, db: Session = Depends(get_db)):
    # Broadcast to agents via queue (agents pick this up from the event system)
    await manager.broadcast({
        "agent_id": "system",
        "event_type": "research_refinement",
        "entertainer_id": data.entertainer_id,
        "message": f"User refinement: {data.user_instruction}",
        "instruction": data.user_instruction,
    })
    # Store refinement in DB as an event so the bureau can pick it up
    event = models.AgentEvent(
        agent_id="user",
        event_type="research_refinement",
        message=data.user_instruction,
        entertainer_id=data.entertainer_id,
    )
    db.add(event)
    db.commit()

    if live_sources_configured() and discover_live_venues:
        entertainer = db.query(models.Entertainer).filter(models.Entertainer.id == data.entertainer_id).first()
        if entertainer:
            payload = {
                "id": entertainer.id,
                "name": entertainer.name,
                "type": entertainer.type,
                "genre": entertainer.genre,
                "location": entertainer.location,
                "experience_years": entertainer.experience_years,
                "social_followers": entertainer.social_followers,
                "highlights": entertainer.highlights,
                "current_rate": entertainer.current_rate,
            }
            live_data = discover_live_venues(payload, data.user_instruction)
            discovery_source = "live_research_refinement"
            if (not live_data or not live_data.get("venues")) and curated_opportunity_fallback:
                live_data = curated_opportunity_fallback(payload, data.user_instruction)
                discovery_source = "agent_curated_fallback"
            if live_data and live_data.get("venues"):
                db.query(models.Venue).filter(models.Venue.entertainer_id == data.entertainer_id).delete()
                for v in live_data["venues"]:
                    db.add(models.Venue(
                        entertainer_id=data.entertainer_id,
                        name=v.get("name"),
                        contact_name=v.get("contact_name"),
                        contact_email=v.get("contact_email"),
                        source_url=v.get("source_url"),
                        venue_type=v.get("venue_type"),
                        typical_pay=v.get("typical_pay"),
                        fit_score=v.get("fit_score"),
                        contact_approach=v.get("contact_approach"),
                        why_fits=v.get("why_fits"),
                        specific_examples=json.dumps(v.get("specific_examples", [])),
                    ))
                db.commit()
                mirror_venues(data.entertainer_id, live_data["venues"], source=discovery_source)
                await manager.broadcast({
                    "agent_id": "agent1",
                    "event_type": "complete",
                    "entertainer_id": data.entertainer_id,
                    "message": (
                        f"Live discovery found {len(live_data['venues'])} venues from Gemini/Google/Eventbrite/social sources."
                        if discovery_source == "live_research_refinement"
                        else f"Live provider quota unavailable; loaded {len(live_data['venues'])} agent-curated fallback opportunities."
                    ),
                })
                return {
                    "ok": True,
                    "live_discovery": discovery_source == "live_research_refinement",
                    "fallback_discovery": discovery_source == "agent_curated_fallback",
                    "venues_created": len(live_data["venues"]),
                }

    return {"ok": True, "live_discovery": False}


@router.post("/strategy-update")
async def strategy_update(data: schemas.StrategyUpdateRequest, db: Session = Depends(get_db)):
    await manager.broadcast({
        "agent_id": "system",
        "event_type": "strategy_update",
        "entertainer_id": data.entertainer_id,
        "target_id": data.target_id,
        "message": f"Strategy update for target {data.target_id}: {data.strategy_instruction}",
        "instruction": data.strategy_instruction,
    })
    event = models.AgentEvent(
        agent_id="user",
        event_type="strategy_update",
        message=data.strategy_instruction,
        entertainer_id=data.entertainer_id,
        target_id=data.target_id,
    )
    db.add(event)
    db.commit()
    return {"ok": True}
