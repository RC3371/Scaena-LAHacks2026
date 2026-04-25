from datetime import datetime
from fastapi import APIRouter, HTTPException
from models import GenerateFollowUpsRequest
from database import get_db, row_to_dict, rows_to_list
from agents.agent4_followup import schedule_followups_for_profile

router = APIRouter(prefix="/api/followups", tags=["followups"])


@router.post("/generate")
def generate_followups(data: GenerateFollowUpsRequest):
    with get_db() as conn:
        profile = row_to_dict(conn.execute("SELECT * FROM profiles WHERE id = ?", (data.profile_id,)).fetchone())
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    scheduled = schedule_followups_for_profile(data.profile_id)
    return {"scheduled": scheduled, "count": len(scheduled)}


@router.get("/{profile_id}")
def list_followups(profile_id: int, status: str = None):
    query = """
        SELECT f.*, pr.name as prospect_name, pr.type as venue_type, pr.location as venue_location,
               p.subject as original_subject
        FROM follow_ups f
        JOIN prospects pr ON f.prospect_id = pr.id
        JOIN pitches p ON f.pitch_id = p.id
        WHERE f.profile_id = ?
    """
    params = [profile_id]
    if status:
        query += " AND f.status = ?"
        params.append(status)
    query += " ORDER BY f.scheduled_for ASC"
    with get_db() as conn:
        followups = rows_to_list(conn.execute(query, params).fetchall())
    return followups


@router.post("/{followup_id}/send")
def mark_followup_sent(followup_id: int):
    now = datetime.now().isoformat()
    with get_db() as conn:
        followup = row_to_dict(conn.execute("SELECT * FROM follow_ups WHERE id = ?", (followup_id,)).fetchone())
        if not followup:
            raise HTTPException(status_code=404, detail="Follow-up not found")
        conn.execute(
            "UPDATE follow_ups SET status = 'sent', sent_at = ? WHERE id = ?",
            (now, followup_id),
        )
        conn.execute(
            "UPDATE prospects SET status = 'follow_up' WHERE id = ?",
            (followup["prospect_id"],),
        )
    return {"message": "Follow-up marked as sent", "sent_at": now}


@router.post("/{followup_id}/cancel")
def cancel_followup(followup_id: int):
    with get_db() as conn:
        conn.execute("UPDATE follow_ups SET status = 'cancelled' WHERE id = ?", (followup_id,))
    return {"message": "Follow-up cancelled"}


@router.get("/{profile_id}/due")
def get_due_followups(profile_id: int):
    now = datetime.now().isoformat()
    with get_db() as conn:
        due = rows_to_list(conn.execute(
            """SELECT f.*, pr.name as prospect_name, pr.type as venue_type
               FROM follow_ups f
               JOIN prospects pr ON f.prospect_id = pr.id
               WHERE f.profile_id = ? AND f.status = 'scheduled' AND f.scheduled_for <= ?
               ORDER BY f.scheduled_for ASC""",
            (profile_id, now),
        ).fetchall())
    return due
