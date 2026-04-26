from agents.agent_runtime import Model
from typing import List, Optional

# Well-known agent addresses (set before bureau starts)
AGENT1_ADDRESS = "agent1qscaenamarketresearch"
AGENT2_ADDRESS = "agent1qscaenaoutreachpitching"
AGENT3_ADDRESS = "agent1qscaenaanalyticslearning"
AGENT4_ADDRESS = "agent1qscaenapipelinerebook"


class MarketResearchResult(Model):
    entertainer_id: str
    entertainer_type: str
    market_rate_low: float
    market_rate_high: float
    recommended_rate: float
    venues: List[dict]
    market_insights: str
    pricing_trend: str
    timestamp: str


class ResearchRefinement(Model):
    entertainer_id: str
    user_instruction: str
    timestamp: str


class OutreachBatchSent(Model):
    entertainer_id: str
    batch_id: str
    pitches_sent: int
    venue_ids: List[str]
    timestamp: str


class MessageSentToTarget(Model):
    entertainer_id: str
    target_id: str
    message_type: str
    subject: str
    body: str
    timestamp: str


class TargetReply(Model):
    entertainer_id: str
    target_id: str
    reply_body: str
    reply_sentiment: Optional[str] = None
    timestamp: str


class LearningInsights(Model):
    entertainer_id: str
    best_venue_types: List[str]
    best_pitch_angle: str
    accepted_rate: float
    optimal_price: float
    avoid_segments: List[str]
    insights_narrative: str
    round_number: int


class AgentThinkingStep(Model):
    agent_id: str
    entertainer_id: str
    target_id: Optional[str] = None
    step: str
    conclusion: Optional[str] = None
    timestamp: str


class FollowUpEngagement(Model):
    entertainer_id: str
    venue_id: str
    followup_number: int
    response_received: bool
    response_type: Optional[str] = None
    timestamp: str


class BookingConversationUpdate(Model):
    entertainer_id: str
    target_id: str
    booking_id: str
    message_sent: str
    response_received: Optional[str] = None
    conversation_stage: str
    timestamp: str


class TriggerResearch(Model):
    entertainer_id: str
    round_number: int


class TargetStrategyUpdate(Model):
    entertainer_id: str
    target_id: str
    strategy_instruction: str
    timestamp: str
