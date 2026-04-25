from fastapi import APIRouter, HTTPException
from models import ProspectCreate, ProspectStatusUpdate
from database import get_db, row_to_dict, rows_to_list

router = APIRouter(prefix="/api/prospects", tags=["prospects"])


@router.get("/{profile_id}")
def list_prospects(profile_id: int, status: str = None, type: str = None):
    query = "SELECT * FROM prospects WHERE profile_id = ?"
    params = [profile_id]
    if status:
        query += " AND status = ?"
        params.append(status)
    if type:
        query += " AND type = ?"
        params.append(type)
    query += " ORDER BY created_at DESC"
    with get_db() as conn:
        prospects = rows_to_list(conn.execute(query, params).fetchall())
    return prospects


@router.post("")
def create_prospect(data: ProspectCreate):
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO prospects (profile_id, name, type, location, contact_email, contact_name,
               typical_pay_min, typical_pay_max, notes, source)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (data.profile_id, data.name, data.type, data.location, data.contact_email,
             data.contact_name, data.typical_pay_min, data.typical_pay_max, data.notes, data.source),
        )
        prospect = row_to_dict(conn.execute("SELECT * FROM prospects WHERE id = ?", (cursor.lastrowid,)).fetchone())
    return prospect


@router.get("/detail/{prospect_id}")
def get_prospect(prospect_id: int):
    with get_db() as conn:
        prospect = row_to_dict(conn.execute("SELECT * FROM prospects WHERE id = ?", (prospect_id,)).fetchone())
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    return prospect


@router.put("/{prospect_id}/status")
def update_prospect_status(prospect_id: int, data: ProspectStatusUpdate):
    valid_statuses = ["new", "pitched", "responded", "booked", "declined", "follow_up"]
    if data.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    with get_db() as conn:
        conn.execute("UPDATE prospects SET status = ? WHERE id = ?", (data.status, prospect_id))
        prospect = row_to_dict(conn.execute("SELECT * FROM prospects WHERE id = ?", (prospect_id,)).fetchone())
    return prospect


@router.delete("/{prospect_id}")
def delete_prospect(prospect_id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM prospects WHERE id = ?", (prospect_id,))
    return {"message": "Prospect deleted"}
