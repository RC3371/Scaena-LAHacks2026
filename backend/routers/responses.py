from fastapi import APIRouter, HTTPException
from models import RecordResponseRequest
from database import get_db, row_to_dict, rows_to_list
from agents.agent4_followup import generate_objection_response

router = APIRouter(prefix="/api/responses", tags=["responses"])

VALID_RESPONSE_TYPES = ["interested", "not_interested", "maybe", "booked", "negotiating", "no_response"]


@router.post("")
def record_response(data: RecordResponseRequest):
    if data.response_type not in VALID_RESPONSE_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid response type. Must be one of: {VALID_RESPONSE_TYPES}")

    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO pitch_responses (pitch_id, prospect_id, response_type, response_text)
               VALUES (?, ?, ?, ?)""",
            (data.pitch_id, data.prospect_id, data.response_type, data.response_text),
        )
        response_id = cursor.lastrowid

        status_map = {
            "interested": "responded",
            "booked": "booked",
            "negotiating": "responded",
            "not_interested": "declined",
            "maybe": "responded",
        }
        prospect_status = status_map.get(data.response_type, "responded")
        conn.execute("UPDATE prospects SET status = ? WHERE id = ?", (prospect_status, data.prospect_id))

        if data.response_type == "booked":
            conn.execute("UPDATE pitches SET status = 'booked' WHERE id = ?", (data.pitch_id,))
        else:
            conn.execute("UPDATE pitches SET status = 'responded' WHERE id = ?", (data.pitch_id,))

        response = row_to_dict(conn.execute("SELECT * FROM pitch_responses WHERE id = ?", (response_id,)).fetchone())

    return response


@router.get("/{profile_id}")
def list_responses(profile_id: int):
    with get_db() as conn:
        responses = rows_to_list(conn.execute(
            """SELECT pr.*, p.subject as pitch_subject, pros.name as venue_name, pros.type as venue_type
               FROM pitch_responses pr
               JOIN pitches p ON pr.pitch_id = p.id
               JOIN prospects pros ON pr.prospect_id = pros.id
               WHERE p.profile_id = ?
               ORDER BY pr.responded_at DESC""",
            (profile_id,)
        ).fetchall())
    return responses


@router.post("/handle-objection")
def handle_objection(pitch_id: int, objection_type: str, objection_text: str):
    with get_db() as conn:
        pitch = row_to_dict(conn.execute("SELECT * FROM pitches WHERE id = ?", (pitch_id,)).fetchone())
        if not pitch:
            raise HTTPException(status_code=404, detail="Pitch not found")
        profile = row_to_dict(conn.execute("SELECT * FROM profiles WHERE id = ?", (pitch["profile_id"],)).fetchone())
        prospect = row_to_dict(conn.execute("SELECT * FROM prospects WHERE id = ?", (pitch["prospect_id"],)).fetchone())

    counter_offers = generate_objection_response(
        profile, prospect, objection_type, objection_text, pitch["proposed_rate"]
    )
    return counter_offers
