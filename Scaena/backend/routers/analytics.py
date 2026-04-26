from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database import get_db
from backend import models, schemas
from backend.services.conversation_visibility import visible_conversation_messages
from typing import List
from datetime import datetime
import json

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _json_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [str(item) for item in parsed if str(item).strip()]
    except Exception:
        pass
    return [str(raw)]


def _venue_type_for_pitch(db: Session, entertainer_id: str, pitch: models.Pitch | None) -> str:
    if not pitch:
        return "Unknown"
    if pitch.venue_id:
        venue = db.query(models.Venue).filter(models.Venue.id == pitch.venue_id).first()
        if venue and venue.venue_type:
            return venue.venue_type
    venue = (
        db.query(models.Venue)
        .filter(models.Venue.entertainer_id == entertainer_id, models.Venue.name == pitch.venue_name)
        .order_by(models.Venue.created_at.desc())
        .first()
    )
    return venue.venue_type if venue and venue.venue_type else (pitch.venue_name or "Unknown")


def _chat_history_intel(entertainer_id: str, db: Session) -> dict:
    convs = (
        db.query(models.Conversation)
        .filter(models.Conversation.entertainer_id == entertainer_id)
        .order_by(models.Conversation.updated_at.desc(), models.Conversation.created_at.desc())
        .all()
    )
    venue_stats: dict[str, dict] = {}
    recent_conversations = []
    what_worked: list[str] = []
    avoid_segments: set[str] = set()
    accepted_rates: list[float] = []
    proposed_rates: list[float] = []
    inbound_count = 0
    outbound_count = 0
    total_messages = 0
    latest_message_at: datetime | None = None

    for conv in convs:
        pitch = db.query(models.Pitch).filter(models.Pitch.id == conv.pitch_id).first() if conv.pitch_id else None
        venue_type = _venue_type_for_pitch(db, entertainer_id, pitch)
        stats = venue_stats.setdefault(venue_type, {"sent": 0, "responded": 0, "accepted": 0, "rejected": 0})
        if pitch and pitch.status in {"sent", "responded", "accepted", "rejected", "booked", "draft"}:
            stats["sent"] += 1
        if pitch and pitch.proposed_rate:
            proposed_rates.append(float(pitch.proposed_rate))
        if pitch and pitch.negotiated_price:
            accepted_rates.append(float(pitch.negotiated_price))
        if pitch and pitch.response_type:
            stats["responded"] += 1
            if pitch.response_type == "accepted":
                stats["accepted"] += 1
            if pitch.response_type == "rejected":
                stats["rejected"] += 1

        messages = visible_conversation_messages(db, conv)
        inbound = [msg for msg in messages if msg.direction == "inbound"]
        outbound = [msg for msg in messages if msg.direction == "outbound"]
        inbound_count += len(inbound)
        outbound_count += len(outbound)
        total_messages += len(messages)
        if inbound:
            stats["responded"] = max(stats["responded"], 1)
        if conv.interest_level == "high":
            stats["accepted"] = max(stats["accepted"], 1 if pitch and pitch.response_type == "accepted" else stats["accepted"])
        if conv.what_worked:
            what_worked.append(conv.what_worked)

        if messages:
            newest = max((msg.created_at for msg in messages if msg.created_at), default=None)
            if newest and (latest_message_at is None or newest > latest_message_at):
                latest_message_at = newest

        if pitch and pitch.response_type == "accepted":
            accepted_rates.append(float(pitch.negotiated_price or pitch.proposed_rate or 0))
        if pitch and pitch.response_type == "rejected":
            avoid_segments.add(venue_type)

        latest = messages[-1] if messages else None
        recent_conversations.append({
            "id": conv.id,
            "venue_name": conv.venue_name,
            "venue_type": venue_type,
            "message_count": len(messages),
            "inbound_messages": len(inbound),
            "outbound_messages": len(outbound),
            "latest_direction": latest.direction if latest else None,
            "latest_message_at": latest.created_at.isoformat() if latest and latest.created_at else None,
            "interest_level": conv.interest_level,
            "what_to_do_next": conv.what_to_do_next,
            "pitch_status": pitch.status if pitch else None,
            "response_type": pitch.response_type if pitch else None,
        })

    ranked_types = sorted(
        venue_stats.items(),
        key=lambda item: (
            item[1]["accepted"],
            item[1]["responded"] / max(item[1]["sent"], 1),
            item[1]["responded"],
        ),
        reverse=True,
    )
    best_venue_types = [name for name, stats in ranked_types if stats["responded"] or stats["accepted"]][:4]
    if not best_venue_types:
        best_venue_types = [name for name, _ in ranked_types[:3]] or ["College", "Music Venue", "Bar"]

    if not avoid_segments:
        avoid_segments = {
            name
            for name, stats in venue_stats.items()
            if stats["sent"] >= 2 and stats["responded"] == 0
        }

    optimal_price = 0.0
    useful_rates = [rate for rate in accepted_rates if rate > 0] or [rate for rate in proposed_rates if rate > 0]
    if useful_rates:
        optimal_price = round(sum(useful_rates) / len(useful_rates) / 25) * 25

    if what_worked:
        best_pitch_angle = what_worked[0]
    elif inbound_count:
        best_pitch_angle = "Reference the venue's actual reply, keep the next ask concise, and preserve agreed rate/date details."
    else:
        best_pitch_angle = "Use venue-specific fit, clear rate, and direct booking-team language."

    insights_narrative = (
        f"Auto-ingested from {total_messages} stored Outreach/Gmail messages across {len(convs)} conversations. "
        f"Agent 3 is using real chat history, latest replies, accepted rates, and venue response patterns instead of waiting for manual reply logs. "
        f"Current strongest lane: {', '.join(best_venue_types[:3])}."
    )

    thinking_steps = [
        f"Scanned {len(convs)} conversations from Outreach/Gmail history",
        f"Read {inbound_count} recipient messages and {outbound_count} team messages",
        f"Ranked venue lanes: {', '.join(best_venue_types[:3])}",
        "Updated extracted intel from chat history automatically",
    ]

    return {
        "source": "chat_history",
        "conversations_scanned": len(convs),
        "messages_scanned": total_messages,
        "inbound_messages": inbound_count,
        "outbound_messages": outbound_count,
        "latest_message_at": latest_message_at,
        "best_venue_types": best_venue_types,
        "avoid_segments": sorted(avoid_segments),
        "best_pitch_angle": best_pitch_angle,
        "optimal_price": float(optimal_price),
        "insights_narrative": insights_narrative,
        "recent_conversations": recent_conversations[:10],
        "thinking_steps": thinking_steps,
    }


def _latest_insight(entertainer_id: str, db: Session) -> models.LearningInsight | None:
    return (
        db.query(models.LearningInsight)
        .filter(models.LearningInsight.entertainer_id == entertainer_id)
        .order_by(models.LearningInsight.created_at.desc())
        .first()
    )


@router.get("/summary/{entertainer_id}", response_model=schemas.AnalyticsSummaryOut)
def analytics_summary(entertainer_id: str, db: Session = Depends(get_db)):
    pitches = db.query(models.Pitch).filter(models.Pitch.entertainer_id == entertainer_id).all()
    total_pitches = len(pitches)
    sent_statuses = ("sent", "responded", "accepted", "rejected", "booked")
    sent = [p for p in pitches if p.status in sent_statuses]
    responded = [p for p in pitches if p.response_type is not None]
    accepted = [p for p in pitches if p.response_type == "accepted"]
    rejected = [p for p in pitches if p.response_type == "rejected"]
    negotiating = [p for p in pitches if p.response_type == "negotiating"]

    total_responses = len(responded)
    response_rate = total_responses / max(len(sent), 1)

    # By venue type (using venue_name as proxy)
    by_venue: dict = {}
    for p in pitches:
        vt = p.venue_name or "Other"
        if vt not in by_venue:
            by_venue[vt] = {"sent": 0, "responded": 0, "accepted": 0}
        if p.status in sent_statuses:
            by_venue[vt]["sent"] += 1
        if p.response_type:
            by_venue[vt]["responded"] += 1
        if p.response_type == "accepted":
            by_venue[vt]["accepted"] += 1

    # Price data
    rates = [p.proposed_rate for p in pitches if p.proposed_rate]
    negotiated = [p.negotiated_price for p in pitches if p.negotiated_price]
    price_data = {
        "avg_proposed": sum(rates) / len(rates) if rates else 0,
        "avg_negotiated": sum(negotiated) / len(negotiated) if negotiated else 0,
    }

    # Follow-up response rates
    fu_results = db.query(models.FollowUpResult).filter(
        models.FollowUpResult.entertainer_id == entertainer_id
    ).all()

    def fu_rate(n):
        group = [r for r in fu_results if r.followup_number == n]
        if not group:
            return 0.0
        return sum(1 for r in group if r.response_received) / len(group)

    return schemas.AnalyticsSummaryOut(
        total_pitches=total_pitches,
        total_responses=total_responses,
        response_rate=response_rate,
        accepted=len(accepted),
        rejected=len(rejected),
        negotiating=len(negotiating),
        by_venue_type=by_venue,
        price_data=price_data,
        followup1_rate=fu_rate(1),
        followup2_rate=fu_rate(2),
        followup3_rate=fu_rate(3),
    )


@router.post("/insights")
def save_insights(data: schemas.InsightsCreate, db: Session = Depends(get_db)):
    insight = models.LearningInsight(
        entertainer_id=data.entertainer_id,
        round_number=data.round_number,
        best_venue_types=json.dumps(data.best_venue_types),
        avoid_segments=json.dumps(data.avoid_segments),
        best_pitch_angle=data.best_pitch_angle,
        optimal_price=data.optimal_price,
        insights_narrative=data.insights_narrative,
    )
    db.add(insight)
    db.commit()
    return {"ok": True}


@router.get("/insights/{entertainer_id}", response_model=List[schemas.InsightsOut])
def get_insights(entertainer_id: str, db: Session = Depends(get_db)):
    return (
        db.query(models.LearningInsight)
        .filter(models.LearningInsight.entertainer_id == entertainer_id)
        .order_by(models.LearningInsight.created_at.desc())
        .limit(10)
        .all()
    )


@router.post("/auto-ingest/{entertainer_id}")
def auto_ingest_chat_history(entertainer_id: str, db: Session = Depends(get_db)):
    """Materialize Agent 3 insights from already-stored Outreach/Gmail chat history."""
    intel = _chat_history_intel(entertainer_id, db)
    latest = _latest_insight(entertainer_id, db)
    latest_message_at = intel.get("latest_message_at")

    should_create = bool(intel["messages_scanned"]) and (
        latest is None
        or (
            latest_message_at is not None
            and latest.created_at is not None
            and latest.created_at < latest_message_at
        )
        or (
            latest is not None
            and "Auto-ingested from" not in (latest.insights_narrative or "")
            and intel["inbound_messages"] > 0
        )
    )

    created = False
    if should_create:
        latest_round = (
            db.query(func.max(models.LearningInsight.round_number))
            .filter(models.LearningInsight.entertainer_id == entertainer_id)
            .scalar()
            or 0
        )
        insight = models.LearningInsight(
            entertainer_id=entertainer_id,
            round_number=int(latest_round) + 1,
            best_venue_types=json.dumps(intel["best_venue_types"]),
            avoid_segments=json.dumps(intel["avoid_segments"]),
            best_pitch_angle=intel["best_pitch_angle"],
            optimal_price=intel["optimal_price"],
            insights_narrative=intel["insights_narrative"],
        )
        db.add(insight)
        db.commit()
        latest = insight
        created = True

    return {
        "ok": True,
        "created_insight": created,
        "insight_id": latest.id if latest else None,
        **{
            key: value.isoformat() if isinstance(value, datetime) else value
            for key, value in intel.items()
        },
    }
