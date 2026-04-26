from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from datetime import datetime


class EntertainerCreate(BaseModel):
    name: str
    type: str
    genre: Optional[str] = None
    location: Optional[str] = None
    experience_years: Optional[int] = None
    social_followers: Optional[int] = None
    highlights: Optional[str] = None
    links: Optional[str] = None
    current_rate: Optional[float] = None
    outreach_mode: str = "auto_pitch"


class EntertainerUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    genre: Optional[str] = None
    location: Optional[str] = None
    experience_years: Optional[int] = None
    social_followers: Optional[int] = None
    highlights: Optional[str] = None
    links: Optional[str] = None
    current_rate: Optional[float] = None
    outreach_mode: Optional[str] = None
    is_active: Optional[bool] = None


class EntertainerOut(BaseModel):
    id: str
    name: str
    type: str
    genre: Optional[str]
    location: Optional[str]
    experience_years: Optional[int]
    social_followers: Optional[int]
    highlights: Optional[str]
    links: Optional[str]
    current_rate: Optional[float]
    outreach_mode: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class VenueBulkItem(BaseModel):
    name: str
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    source_url: Optional[str] = None
    venue_type: Optional[str] = None
    typical_pay: Optional[str] = None
    fit_score: Optional[float] = None
    contact_approach: Optional[str] = None
    why_fits: Optional[str] = None
    specific_examples: Optional[List[str]] = None


class VenueBulkCreate(BaseModel):
    entertainer_id: str
    venues: List[Dict[str, Any]]
    market_insights: Optional[str] = None
    recommended_rate: Optional[float] = None


class VenueOut(BaseModel):
    id: str
    entertainer_id: str
    name: Optional[str]
    contact_name: Optional[str]
    contact_email: Optional[str]
    source_url: Optional[str]
    venue_type: Optional[str]
    typical_pay: Optional[str]
    fit_score: Optional[float]
    contact_approach: Optional[str]
    why_fits: Optional[str]
    specific_examples: Optional[str]
    research_round: int
    created_at: datetime

    class Config:
        from_attributes = True


class PitchCreate(BaseModel):
    entertainer_id: str
    batch_id: Optional[str] = None
    venue_name: str
    entertainer_type: Optional[str] = None
    recipient_email: Optional[str] = None
    venue_contact_approach: Optional[str] = None
    pitch_subject: str
    pitch_body: str
    proposed_rate: Optional[float] = None
    status: str = "draft"


class PitchGenerateCreate(BaseModel):
    entertainer_id: str
    venue_id: Optional[str] = None
    venue_name: Optional[str] = None
    venue_type: Optional[str] = None
    recipient_email: Optional[str] = None
    venue_contact_approach: Optional[str] = None
    why_fits: Optional[str] = None
    source_url: Optional[str] = None
    specific_examples: Optional[str] = None
    proposed_rate: Optional[float] = None
    status: str = "draft"


class RebookPitchCreate(BaseModel):
    entertainer_id: str
    booking_id: str
    status: str = "draft"


class PitchRegenerateRequest(BaseModel):
    entertainer_id: Optional[str] = None
    strategy_instruction: Optional[str] = None


class PitchUpdate(BaseModel):
    status: Optional[str] = None
    recipient_email: Optional[str] = None
    response_type: Optional[str] = None
    negotiated_price: Optional[float] = None
    sent_at: Optional[datetime] = None
    strategy_note: Optional[str] = None
    pitch_subject: Optional[str] = None
    pitch_body: Optional[str] = None
    followup_count: Optional[int] = None


class PitchOut(BaseModel):
    id: str
    entertainer_id: str
    venue_name: Optional[str]
    entertainer_type: Optional[str]
    recipient_email: Optional[str]
    pitch_subject: Optional[str]
    pitch_body: Optional[str]
    proposed_rate: Optional[float]
    status: str
    followup_count: int
    response_type: Optional[str]
    strategy_note: Optional[str]
    gmail_message_id: Optional[str]
    gmail_thread_id: Optional[str]
    created_at: datetime
    sent_at: Optional[datetime]

    class Config:
        from_attributes = True


class FollowUpCreate(BaseModel):
    pitch_id: str
    entertainer_id: str
    followup_number: int
    subject: str
    body: str
    status: str = "draft"


class FollowUpUpdate(BaseModel):
    status: Optional[str] = None
    sent_at: Optional[datetime] = None


class FollowUpOut(BaseModel):
    id: str
    pitch_id: str
    entertainer_id: str
    followup_number: int
    subject: str
    body: str
    status: str
    sent_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class FollowUpResultCreate(BaseModel):
    entertainer_id: str
    venue_id: str
    followup_number: int
    response_received: bool
    response_type: Optional[str] = None
    timestamp: str


class ReengagementCreate(BaseModel):
    pitch_id: Optional[str] = None
    entertainer_id: Optional[str] = None
    target_id: Optional[str] = None
    subject: str
    body: str
    reason: str
    status: str = "draft"


class ReengagementOut(BaseModel):
    id: str
    pitch_id: Optional[str]
    subject: str
    body: str
    reason: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class BatchCreate(BaseModel):
    entertainer_id: str
    batch_id: str
    pitches_sent: int
    timestamp: str


class ResearchRefinementRequest(BaseModel):
    entertainer_id: str
    user_instruction: str


class StrategyUpdateRequest(BaseModel):
    entertainer_id: str
    target_id: str
    strategy_instruction: str


class ReplyCreate(BaseModel):
    entertainer_id: str
    target_id: str
    reply_body: str
    reply_sentiment: Optional[str] = None


class ConversationAnalysisCreate(BaseModel):
    target_id: str
    entertainer_id: str
    interest_level: str
    signals: List[str]
    what_worked: str
    what_to_do_next: str
    conversion_likelihood: float


class ConversationMessageOut(BaseModel):
    id: str
    direction: str
    message_type: str
    subject: Optional[str]
    body: str
    sentiment: Optional[str]
    gmail_message_id: Optional[str] = None
    gmail_thread_id: Optional[str] = None
    from_email: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationOut(BaseModel):
    id: str
    pitch_id: str
    venue_name: Optional[str]
    interest_level: Optional[str]
    signals: Optional[str]
    what_worked: Optional[str]
    what_to_do_next: Optional[str]
    conversion_likelihood: Optional[float]
    messages: List[ConversationMessageOut] = []

    class Config:
        from_attributes = True


class BookingMessageCreate(BaseModel):
    booking_id: str
    entertainer_id: str
    target_id: str
    stage: str
    subject: str
    body: str
    status: str = "draft"


class BookingConversationUpdate(BaseModel):
    target_id: str
    entertainer_id: str
    booking_id: str
    message_sent: str
    response_received: Optional[str] = None
    conversation_stage: str
    timestamp: str


class BookingPipelineUpdate(BaseModel):
    conversation_stage: Optional[str] = None
    agreed_rate: Optional[float] = None
    show_date: Optional[str] = None
    logistics_checklist: Optional[Dict[str, bool]] = None
    show_summary: Optional[str] = None
    post_show_notes: Optional[str] = None
    crowd_size: Optional[int] = None
    audience_reaction: Optional[str] = None
    payout_received: Optional[bool] = None
    venue_satisfaction: Optional[str] = None
    rebook_recommended: Optional[bool] = None
    next_reminder_at: Optional[datetime] = None


class PerformanceResolve(BaseModel):
    post_show_notes: Optional[str] = None
    crowd_size: Optional[int] = None
    audience_reaction: Optional[str] = None
    payout_received: Optional[bool] = None
    venue_satisfaction: Optional[str] = None
    rebook_recommended: Optional[bool] = True


class BookingOut(BaseModel):
    id: str
    entertainer_id: str
    pitch_id: str
    target_id: str
    venue_name: str
    agreed_rate: Optional[float]
    show_date: Optional[str]
    conversation_stage: str
    logistics_checklist: Optional[Any] = None
    show_summary: Optional[str] = None
    post_show_notes: Optional[str] = None
    crowd_size: Optional[int] = None
    audience_reaction: Optional[str] = None
    payout_received: Optional[bool] = None
    venue_satisfaction: Optional[str] = None
    rebook_recommended: Optional[bool] = None
    next_reminder_at: Optional[datetime] = None
    performance_completed_at: Optional[datetime] = None
    rebooking_sent: bool
    pipeline_health: Optional[str] = None
    pipeline_reminders: Optional[Any] = None
    next_action: Optional[str] = None
    days_until_show: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BookingMessageOut(BaseModel):
    id: str
    booking_id: str
    stage: str
    subject: str
    body: str
    status: str
    sent_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class InsightsCreate(BaseModel):
    entertainer_id: str
    round_number: int
    best_venue_types: List[str]
    avoid_segments: List[str]
    best_pitch_angle: str
    optimal_price: float
    insights_narrative: str


class InsightsOut(BaseModel):
    id: str
    entertainer_id: str
    round_number: int
    best_venue_types: str
    avoid_segments: str
    best_pitch_angle: str
    optimal_price: float
    insights_narrative: str
    created_at: datetime

    class Config:
        from_attributes = True


class AnalyticsSummaryOut(BaseModel):
    total_pitches: int
    total_responses: int
    response_rate: float
    accepted: int
    rejected: int
    negotiating: int
    by_venue_type: Dict[str, Any]
    price_data: Dict[str, Any]
    followup1_rate: float
    followup2_rate: float
    followup3_rate: float


class AgentEventCreate(BaseModel):
    agent_id: str
    event_type: str
    message: str
    entertainer_id: Optional[str] = None
    target_id: Optional[str] = None
    conclusion: Optional[str] = None


class AgentEventOut(BaseModel):
    id: str
    agent_id: str
    event_type: str
    message: str
    entertainer_id: Optional[str]
    target_id: Optional[str]
    conclusion: Optional[str]
    extra: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AgentStatusOut(BaseModel):
    agent_id: str
    name: str
    status: str
    last_event: Optional[str]
