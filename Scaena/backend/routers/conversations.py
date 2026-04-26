from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend import models, schemas
from backend.websocket_manager import manager
import json

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("/{target_id}")
def get_conversation(target_id: str, db: Session = Depends(get_db)):
    conv = db.query(models.Conversation).filter(models.Conversation.id == target_id).first()
    if not conv:
        conv = db.query(models.Conversation).filter(models.Conversation.pitch_id == target_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    msgs = (
        db.query(models.ConversationMessage)
        .filter(models.ConversationMessage.conversation_id == conv.id)
        .order_by(models.ConversationMessage.created_at)
        .all()
    )
    # Get initial pitch body for agent analysis
    pitch = db.query(models.Pitch).filter(models.Pitch.id == conv.pitch_id).first()
    return {
        "id": conv.id,
        "pitch_id": conv.pitch_id,
        "venue_name": conv.venue_name,
        "interest_level": conv.interest_level,
        "signals": json.loads(conv.signals) if conv.signals else [],
        "what_worked": conv.what_worked,
        "what_to_do_next": conv.what_to_do_next,
        "conversion_likelihood": conv.conversion_likelihood,
        "initial_pitch": pitch.pitch_body if pitch else "",
        "messages": [
            {
                "id": m.id,
                "direction": m.direction,
                "message_type": m.message_type,
                "subject": m.subject,
                "body": m.body,
                "sentiment": m.sentiment,
                "gmail_message_id": m.gmail_message_id,
                "gmail_thread_id": m.gmail_thread_id,
                "from_email": m.from_email,
                "created_at": m.created_at.isoformat(),
            }
            for m in msgs
        ],
    }


@router.get("/by-pitch/{pitch_id}")
def get_conversation_by_pitch(pitch_id: str, db: Session = Depends(get_db)):
    conv = db.query(models.Conversation).filter(models.Conversation.pitch_id == pitch_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return get_conversation(conv.id, db)


@router.post("/reply")
async def log_reply(data: schemas.ReplyCreate, db: Session = Depends(get_db)):
    conv = db.query(models.Conversation).filter(models.Conversation.id == data.target_id).first()
    if not conv:
        conv = db.query(models.Conversation).filter(models.Conversation.pitch_id == data.target_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    msg = models.ConversationMessage(
        conversation_id=conv.id,
        direction="inbound",
        message_type="reply",
        body=data.reply_body,
        sentiment=data.reply_sentiment,
    )
    db.add(msg)
    db.commit()
    # Broadcast to trigger Agent 3 analysis
    await manager.broadcast({
        "agent_id": "system",
        "event_type": "reply_logged",
        "entertainer_id": data.entertainer_id,
        "target_id": conv.id,
        "message": f"Reply logged from {conv.venue_name}",
        "reply_body": data.reply_body,
    })
    # Store as agent event so bureau can pick it up
    event = models.AgentEvent(
        agent_id="user",
        event_type="reply_logged",
        message=data.reply_body,
        entertainer_id=data.entertainer_id,
        target_id=conv.id,
    )
    db.add(event)
    db.commit()
    return {"ok": True}


@router.post("/analysis")
def save_analysis(data: schemas.ConversationAnalysisCreate, db: Session = Depends(get_db)):
    conv = db.query(models.Conversation).filter(models.Conversation.id == data.target_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    import json
    conv.interest_level = data.interest_level
    conv.signals = json.dumps(data.signals)
    conv.what_worked = data.what_worked
    conv.what_to_do_next = data.what_to_do_next
    conv.conversion_likelihood = data.conversion_likelihood
    db.commit()
    return {"ok": True}


@router.post("/booking-update")
def booking_update(data: schemas.BookingConversationUpdate, db: Session = Depends(get_db)):
    booking = db.query(models.Booking).filter(models.Booking.id == data.booking_id).first()
    if booking:
        booking.conversation_stage = data.conversation_stage
        db.commit()
    return {"ok": True}


@router.get("/list/{entertainer_id}")
def list_conversations(entertainer_id: str, db: Session = Depends(get_db)):
    convs = (
        db.query(models.Conversation)
        .filter(models.Conversation.entertainer_id == entertainer_id)
        .all()
    )
    result = []
    for conv in convs:
        pitch = db.query(models.Pitch).filter(models.Pitch.id == conv.pitch_id).first()
        msg_count = db.query(models.ConversationMessage).filter(
            models.ConversationMessage.conversation_id == conv.id
        ).count()
        result.append({
            "id": conv.id,
            "pitch_id": conv.pitch_id,
            "venue_name": conv.venue_name,
            "interest_level": conv.interest_level,
            "what_to_do_next": conv.what_to_do_next,
            "conversion_likelihood": conv.conversion_likelihood,
            "pitch_status": pitch.status if pitch else None,
            "pitch_response_type": pitch.response_type if pitch else None,
            "proposed_rate": pitch.proposed_rate if pitch else None,
            "fit_score": None,
            "message_count": msg_count,
        })
    return result
