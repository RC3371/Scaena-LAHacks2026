from fastapi import APIRouter, HTTPException
from models import ProfileCreate, ProfileUpdate
from database import get_db, row_to_dict, rows_to_list

router = APIRouter(prefix="/api/profiles", tags=["profiles"])


@router.post("")
def create_profile(data: ProfileCreate):
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO profiles (name, entertainer_type, genre_style, experience_years, shows_count,
               location, touring_region, rate_min, rate_max, youtube_url, instagram_url, instagram_followers, bio)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (data.name, data.entertainer_type, data.genre_style, data.experience_years, data.shows_count,
             data.location, data.touring_region, data.rate_min, data.rate_max,
             data.youtube_url, data.instagram_url, data.instagram_followers, data.bio),
        )
        profile_id = cursor.lastrowid
        profile = row_to_dict(conn.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,)).fetchone())
    return profile


@router.get("")
def list_profiles():
    with get_db() as conn:
        profiles = rows_to_list(conn.execute("SELECT * FROM profiles ORDER BY created_at DESC").fetchall())
    return profiles


@router.get("/{profile_id}")
def get_profile(profile_id: int):
    with get_db() as conn:
        profile = row_to_dict(conn.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,)).fetchone())
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.put("/{profile_id}")
def update_profile(profile_id: int, data: ProfileUpdate):
    fields = {k: v for k, v in data.model_dump().items() if v is not None}
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [profile_id]
    with get_db() as conn:
        conn.execute(f"UPDATE profiles SET {set_clause} WHERE id = ?", values)
        profile = row_to_dict(conn.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,)).fetchone())
    return profile


@router.delete("/{profile_id}")
def delete_profile(profile_id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
    return {"message": "Profile deleted"}
