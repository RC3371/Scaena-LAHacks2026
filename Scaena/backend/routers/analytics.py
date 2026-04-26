from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database import get_db
from backend import models, schemas
from typing import List
import json

router = APIRouter(prefix="/analytics", tags=["analytics"])


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
