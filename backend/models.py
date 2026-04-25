from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ProfileCreate(BaseModel):
    name: str
    entertainer_type: str
    genre_style: Optional[str] = None
    experience_years: int = 0
    shows_count: int = 0
    location: Optional[str] = None
    touring_region: Optional[str] = None
    rate_min: float = 0
    rate_max: float = 0
    youtube_url: Optional[str] = None
    instagram_url: Optional[str] = None
    instagram_followers: int = 0
    bio: Optional[str] = None


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    entertainer_type: Optional[str] = None
    genre_style: Optional[str] = None
    experience_years: Optional[int] = None
    shows_count: Optional[int] = None
    location: Optional[str] = None
    touring_region: Optional[str] = None
    rate_min: Optional[float] = None
    rate_max: Optional[float] = None
    youtube_url: Optional[str] = None
    instagram_url: Optional[str] = None
    instagram_followers: Optional[int] = None
    bio: Optional[str] = None


class ProspectCreate(BaseModel):
    profile_id: int
    name: str
    type: str
    location: Optional[str] = None
    contact_email: Optional[str] = None
    contact_name: Optional[str] = None
    typical_pay_min: float = 0
    typical_pay_max: float = 0
    notes: Optional[str] = None
    source: str = "manual"


class ProspectStatusUpdate(BaseModel):
    status: str


class GeneratePitchesRequest(BaseModel):
    profile_id: int
    prospect_ids: List[int]
    proposed_rate: Optional[float] = None


class PitchSendRequest(BaseModel):
    pitch_ids: List[int]


class RecordResponseRequest(BaseModel):
    pitch_id: int
    prospect_id: int
    response_type: str
    response_text: Optional[str] = None


class GenerateFollowUpsRequest(BaseModel):
    profile_id: int


class MarketResearchRequest(BaseModel):
    profile_id: int


class AnalyticsRequest(BaseModel):
    profile_id: int
