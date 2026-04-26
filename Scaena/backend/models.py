from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from backend.database import Base


def _uuid():
    return str(uuid.uuid4())


class Entertainer(Base):
    __tablename__ = "entertainers"
    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    genre = Column(String)
    location = Column(String)
    experience_years = Column(Integer)
    social_followers = Column(Integer)
    highlights = Column(Text)
    links = Column(Text)
    current_rate = Column(Float)
    outreach_mode = Column(String, default="auto_pitch")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Venue(Base):
    __tablename__ = "venues"
    id = Column(String, primary_key=True, default=_uuid)
    entertainer_id = Column(String, ForeignKey("entertainers.id"))
    name = Column(String)
    contact_name = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    source_url = Column(String, nullable=True)
    venue_type = Column(String)
    typical_pay = Column(String)
    fit_score = Column(Float)
    contact_approach = Column(String)
    why_fits = Column(Text)
    specific_examples = Column(Text)
    research_round = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)


class Pitch(Base):
    __tablename__ = "pitches"
    id = Column(String, primary_key=True, default=_uuid)
    entertainer_id = Column(String, ForeignKey("entertainers.id"))
    venue_id = Column(String, nullable=True)
    batch_id = Column(String)
    venue_name = Column(String)
    entertainer_type = Column(String)
    recipient_email = Column(String, nullable=True)
    venue_contact_approach = Column(String)
    pitch_subject = Column(String)
    pitch_body = Column(Text)
    proposed_rate = Column(Float)
    status = Column(String, default="draft")
    followup_count = Column(Integer, default=0)
    response_type = Column(String, nullable=True)
    negotiated_price = Column(Float, nullable=True)
    strategy_note = Column(Text, nullable=True)
    gmail_message_id = Column(String, nullable=True)
    gmail_thread_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)


class GmailAccount(Base):
    __tablename__ = "gmail_accounts"
    id = Column(String, primary_key=True, default=_uuid)
    entertainer_id = Column(String, ForeignKey("entertainers.id"))
    email_address = Column(String, nullable=True)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    token_uri = Column(String, default="https://oauth2.googleapis.com/token")
    client_id = Column(String, nullable=True)
    client_secret = Column(Text, nullable=True)
    scopes = Column(Text, nullable=True)
    expiry = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    last_sync_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FollowUp(Base):
    __tablename__ = "followups"
    id = Column(String, primary_key=True, default=_uuid)
    pitch_id = Column(String, ForeignKey("pitches.id"))
    entertainer_id = Column(String, ForeignKey("entertainers.id"))
    followup_number = Column(Integer)
    subject = Column(String)
    body = Column(Text)
    status = Column(String, default="draft")
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Reengagement(Base):
    __tablename__ = "reengagements"
    id = Column(String, primary_key=True, default=_uuid)
    pitch_id = Column(String, ForeignKey("pitches.id"), nullable=True)
    entertainer_id = Column(String, nullable=True)
    target_id = Column(String, nullable=True)
    subject = Column(String)
    body = Column(Text)
    reason = Column(String)
    status = Column(String, default="draft")
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class OutreachBatch(Base):
    __tablename__ = "outreach_batches"
    id = Column(String, primary_key=True, default=_uuid)
    entertainer_id = Column(String, ForeignKey("entertainers.id"))
    batch_id = Column(String)
    pitches_sent = Column(Integer)
    timestamp = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class FollowUpResult(Base):
    __tablename__ = "followup_results"
    id = Column(String, primary_key=True, default=_uuid)
    entertainer_id = Column(String)
    venue_id = Column(String)
    followup_number = Column(Integer)
    response_received = Column(Boolean)
    response_type = Column(String, nullable=True)
    timestamp = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(String, primary_key=True, default=_uuid)
    entertainer_id = Column(String, ForeignKey("entertainers.id"))
    pitch_id = Column(String, ForeignKey("pitches.id"))
    venue_name = Column(String)
    interest_level = Column(String, nullable=True)
    signals = Column(Text, nullable=True)
    what_worked = Column(Text, nullable=True)
    what_to_do_next = Column(Text, nullable=True)
    conversion_likelihood = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"
    id = Column(String, primary_key=True, default=_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"))
    direction = Column(String)  # outbound | inbound
    message_type = Column(String)  # initial_pitch, followup_1, reply, reengagement, post_booking
    subject = Column(String, nullable=True)
    body = Column(Text)
    sentiment = Column(String, nullable=True)
    gmail_message_id = Column(String, nullable=True)
    gmail_thread_id = Column(String, nullable=True)
    from_email = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Booking(Base):
    __tablename__ = "bookings"
    id = Column(String, primary_key=True, default=_uuid)
    entertainer_id = Column(String, ForeignKey("entertainers.id"))
    pitch_id = Column(String, ForeignKey("pitches.id"))
    target_id = Column(String)
    venue_name = Column(String)
    agreed_rate = Column(Float, nullable=True)
    show_date = Column(String, nullable=True)
    conversation_stage = Column(String, default="secured")
    logistics_checklist = Column(Text, nullable=True)
    original_pitch_id = Column(String, nullable=True)
    show_summary = Column(Text, nullable=True)
    post_show_notes = Column(Text, nullable=True)
    crowd_size = Column(Integer, nullable=True)
    audience_reaction = Column(String, nullable=True)
    payout_received = Column(Boolean, default=False)
    venue_satisfaction = Column(String, nullable=True)
    rebook_recommended = Column(Boolean, nullable=True)
    next_reminder_at = Column(DateTime, nullable=True)
    performance_completed_at = Column(DateTime, nullable=True)
    rebooking_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BookingMessage(Base):
    __tablename__ = "booking_messages"
    id = Column(String, primary_key=True, default=_uuid)
    booking_id = Column(String, ForeignKey("bookings.id"))
    entertainer_id = Column(String)
    target_id = Column(String)
    stage = Column(String)
    subject = Column(String)
    body = Column(Text)
    status = Column(String, default="draft")
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class LearningInsight(Base):
    __tablename__ = "learning_insights"
    id = Column(String, primary_key=True, default=_uuid)
    entertainer_id = Column(String, ForeignKey("entertainers.id"))
    round_number = Column(Integer)
    best_venue_types = Column(Text)
    avoid_segments = Column(Text)
    best_pitch_angle = Column(Text)
    optimal_price = Column(Float)
    insights_narrative = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class AgentEvent(Base):
    __tablename__ = "agent_events"
    id = Column(String, primary_key=True, default=_uuid)
    agent_id = Column(String)
    event_type = Column(String)
    message = Column(Text)
    entertainer_id = Column(String, nullable=True)
    target_id = Column(String, nullable=True)
    conclusion = Column(Text, nullable=True)
    extra = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
