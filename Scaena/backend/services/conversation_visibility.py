import re

from sqlalchemy.orm import Session

from backend import models


def _followup_sent(db: Session, pitch_id: str, message_type: str) -> bool:
    match = re.match(r"followup_(\d+)$", message_type or "")
    if not match:
        return False
    followup = (
        db.query(models.FollowUp)
        .filter(models.FollowUp.pitch_id == pitch_id)
        .filter(models.FollowUp.followup_number == int(match.group(1)))
        .order_by(models.FollowUp.created_at.desc())
        .first()
    )
    return bool(followup and followup.status == "sent")


def message_is_visible_in_comms(
    db: Session,
    message: models.ConversationMessage,
    pitch: models.Pitch | None,
) -> bool:
    if message.direction == "inbound":
        return True
    if message.gmail_message_id or message.gmail_thread_id:
        return True

    message_type = message.message_type or ""
    if message_type == "initial_pitch":
        return bool(pitch and (pitch.sent_at or pitch.gmail_message_id or pitch.gmail_thread_id))
    if message_type.startswith("followup_"):
        return bool(pitch and _followup_sent(db, pitch.id, message_type))

    return message_type in {"gmail_reply_sent", "gmail_final_thanks_sent"}


def visible_conversation_messages(db: Session, conv: models.Conversation) -> list[models.ConversationMessage]:
    pitch = db.query(models.Pitch).filter(models.Pitch.id == conv.pitch_id).first()
    messages = (
        db.query(models.ConversationMessage)
        .filter(models.ConversationMessage.conversation_id == conv.id)
        .order_by(models.ConversationMessage.created_at)
        .all()
    )
    return [message for message in messages if message_is_visible_in_comms(db, message, pitch)]
