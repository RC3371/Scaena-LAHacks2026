import json
from datetime import datetime
from fastapi import APIRouter, HTTPException
from models import GeneratePitchesRequest, PitchSendRequest
from database import get_db, row_to_dict, rows_to_list
from agents.agent2_pitch_generator import generate_pitches_batch

router = APIRouter(prefix="/api/pitches", tags=["pitches"])


def _get_analytics_insights(profile_id: int) -> dict:
    with get_db() as conn:
        snapshot = row_to_dict(conn.execute(
            "SELECT snapshot_data FROM analytics_snapshots WHERE profile_id = ? ORDER BY created_at DESC LIMIT 1",
            (profile_id,)
        ).fetchone())
    if snapshot:
        try:
            data = json.loads(snapshot["snapshot_data"])
            return data.get("ai_insights")
        except Exception:
            pass
    return None


@router.post("/generate")
def generate_pitches(data: GeneratePitchesRequest):
    with get_db() as conn:
        profile = row_to_dict(conn.execute("SELECT * FROM profiles WHERE id = ?", (data.profile_id,)).fetchone())
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        prospects = rows_to_list(conn.execute(
            f"SELECT * FROM prospects WHERE id IN ({','.join('?' * len(data.prospect_ids))})",
            data.prospect_ids,
        ).fetchall())

    if not prospects:
        raise HTTPException(status_code=404, detail="No prospects found")

    proposed_rate = data.proposed_rate or profile.get("rate_max", profile.get("rate_min", 300))
    analytics_insights = _get_analytics_insights(data.profile_id)

    pitch_contents = generate_pitches_batch(profile, prospects, proposed_rate, analytics_insights)

    created_pitches = []
    with get_db() as conn:
        for pc in pitch_contents:
            cursor = conn.execute(
                """INSERT INTO pitches (prospect_id, profile_id, subject, body, proposed_rate, status)
                   VALUES (?, ?, ?, ?, ?, 'draft')""",
                (pc["prospect_id"], data.profile_id, pc["subject"], pc["body"], proposed_rate),
            )
            pitch = row_to_dict(conn.execute("SELECT * FROM pitches WHERE id = ?", (cursor.lastrowid,)).fetchone())
            pitch["key_angle"] = pc.get("key_angle", "")
            created_pitches.append(pitch)

    return {"pitches": created_pitches, "count": len(created_pitches)}


@router.get("/{profile_id}")
def list_pitches(profile_id: int, status: str = None):
    query = """
        SELECT p.*, pr.name as prospect_name, pr.type as venue_type, pr.location as venue_location
        FROM pitches p
        JOIN prospects pr ON p.prospect_id = pr.id
        WHERE p.profile_id = ?
    """
    params = [profile_id]
    if status:
        query += " AND p.status = ?"
        params.append(status)
    query += " ORDER BY p.created_at DESC"
    with get_db() as conn:
        pitches = rows_to_list(conn.execute(query, params).fetchall())
    return pitches


@router.get("/detail/{pitch_id}")
def get_pitch(pitch_id: int):
    with get_db() as conn:
        pitch = row_to_dict(conn.execute(
            """SELECT p.*, pr.name as prospect_name, pr.type as venue_type
               FROM pitches p JOIN prospects pr ON p.prospect_id = pr.id
               WHERE p.id = ?""",
            (pitch_id,)
        ).fetchone())
    if not pitch:
        raise HTTPException(status_code=404, detail="Pitch not found")
    return pitch


@router.post("/send")
def mark_pitches_sent(data: PitchSendRequest):
    now = datetime.now().isoformat()
    with get_db() as conn:
        for pitch_id in data.pitch_ids:
            conn.execute(
                "UPDATE pitches SET status = 'sent', sent_at = ? WHERE id = ?",
                (now, pitch_id),
            )
            pitch = row_to_dict(conn.execute("SELECT * FROM pitches WHERE id = ?", (pitch_id,)).fetchone())
            if pitch:
                conn.execute(
                    "UPDATE prospects SET status = 'pitched' WHERE id = ?",
                    (pitch["prospect_id"],),
                )
    return {"message": f"Marked {len(data.pitch_ids)} pitches as sent", "sent_at": now}


@router.put("/{pitch_id}")
def update_pitch(pitch_id: int, subject: str = None, body: str = None):
    fields = {}
    if subject:
        fields["subject"] = subject
    if body:
        fields["body"] = body
    if not fields:
        raise HTTPException(status_code=400, detail="Nothing to update")
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [pitch_id]
    with get_db() as conn:
        conn.execute(f"UPDATE pitches SET {set_clause} WHERE id = ?", values)
        pitch = row_to_dict(conn.execute("SELECT * FROM pitches WHERE id = ?", (pitch_id,)).fetchone())
    return pitch


@router.delete("/{pitch_id}")
def delete_pitch(pitch_id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM pitches WHERE id = ?", (pitch_id,))
    return {"message": "Pitch deleted"}
