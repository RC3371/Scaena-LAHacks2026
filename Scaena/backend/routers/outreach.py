from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from backend.database import get_db
from backend import models, schemas
from backend.websocket_manager import manager
from typing import List, Optional
from datetime import datetime, timedelta
import asyncio
import json

try:
    from agents.research_sources import discover_live_venues, live_sources_configured
except Exception:
    discover_live_venues = None
    live_sources_configured = lambda: False

router = APIRouter(prefix="/outreach", tags=["outreach"])


@router.post("/pitch")
def save_pitch(data: schemas.PitchCreate, db: Session = Depends(get_db)):
    pitch = models.Pitch(**data.model_dump())
    if data.status == "sent":
        pitch.sent_at = datetime.utcnow()
    db.add(pitch)
    db.commit()
    db.refresh(pitch)
    # Auto-create conversation record
    conv = models.Conversation(
        entertainer_id=data.entertainer_id,
        pitch_id=pitch.id,
        venue_name=data.venue_name,
    )
    db.add(conv)
    # Add initial pitch as conversation message
    msg = models.ConversationMessage(
        conversation_id=conv.id,
        direction="outbound",
        message_type="initial_pitch",
        subject=data.pitch_subject,
        body=data.pitch_body,
    )
    db.add(msg)
    db.commit()
    return {"pitch_id": pitch.id}


@router.get("/pitches/{entertainer_id}", response_model=List[schemas.PitchOut])
def list_pitches(entertainer_id: str, status: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(models.Pitch).filter(models.Pitch.entertainer_id == entertainer_id)
    if status:
        q = q.filter(models.Pitch.status == status)
    return q.order_by(models.Pitch.created_at.desc()).all()


@router.get("/pitch-by-target/{target_id}")
def get_pitch_by_target(target_id: str, db: Session = Depends(get_db)):
    conv = db.query(models.Conversation).filter(models.Conversation.id == target_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    pitch = db.query(models.Pitch).filter(models.Pitch.id == conv.pitch_id).first()
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
    for k, v in update.items():
        setattr(pitch, k, v)
    db.commit()
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
    fu = models.FollowUp(**data.model_dump())
    db.add(fu)
    # Increment pitch followup_count
    pitch = db.query(models.Pitch).filter(models.Pitch.id == data.pitch_id).first()
    if pitch:
        pitch.followup_count = (pitch.followup_count or 0) + 1
    # Add to conversation
    conv = db.query(models.Conversation).filter(models.Conversation.pitch_id == data.pitch_id).first()
    if conv:
        msg = models.ConversationMessage(
            conversation_id=conv.id,
            direction="outbound",
            message_type=f"followup_{data.followup_number}",
            subject=data.subject,
            body=data.body,
        )
        db.add(msg)
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
    re = models.Reengagement(**data.model_dump())
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
                await manager.broadcast({
                    "agent_id": "agent1",
                    "event_type": "complete",
                    "entertainer_id": data.entertainer_id,
                    "message": f"Live discovery found {len(live_data['venues'])} venues from Gemini/Google/Eventbrite/social sources.",
                })
                return {"ok": True, "live_discovery": True, "venues_created": len(live_data["venues"])}

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
