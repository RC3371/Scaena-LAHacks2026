import json
from fastapi import APIRouter, HTTPException
from database import get_db, row_to_dict, rows_to_list
from agents.agent3_analytics import compute_analytics

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.post("/run/{profile_id}")
def run_analytics(profile_id: int):
    with get_db() as conn:
        profile = row_to_dict(conn.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,)).fetchone())
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    analytics = compute_analytics(profile_id)

    with get_db() as conn:
        conn.execute(
            "INSERT INTO analytics_snapshots (profile_id, snapshot_data) VALUES (?, ?)",
            (profile_id, json.dumps(analytics)),
        )

    return analytics


@router.get("/{profile_id}")
def get_analytics(profile_id: int):
    with get_db() as conn:
        snapshot = row_to_dict(conn.execute(
            "SELECT * FROM analytics_snapshots WHERE profile_id = ? ORDER BY created_at DESC LIMIT 1",
            (profile_id,)
        ).fetchone())
    if not snapshot:
        analytics = compute_analytics(profile_id)
        return analytics

    data = json.loads(snapshot["snapshot_data"])
    data["snapshot_at"] = snapshot["created_at"]
    return data


@router.get("/{profile_id}/history")
def get_analytics_history(profile_id: int):
    with get_db() as conn:
        snapshots = rows_to_list(conn.execute(
            "SELECT id, profile_id, created_at FROM analytics_snapshots WHERE profile_id = ? ORDER BY created_at DESC LIMIT 10",
            (profile_id,)
        ).fetchall())
    return snapshots


@router.get("/{profile_id}/trend")
def get_analytics_trend(profile_id: int):
    """Return historical analytics to show compounding improvement over time."""
    with get_db() as conn:
        snapshots = rows_to_list(conn.execute(
            "SELECT * FROM analytics_snapshots WHERE profile_id = ? ORDER BY created_at ASC LIMIT 10",
            (profile_id,)
        ).fetchall())

    trend = []
    for snap in snapshots:
        try:
            data = json.loads(snap["snapshot_data"])
            summary = data.get("summary", {})
            trend.append({
                "date": snap["created_at"],
                "total_pitches_sent": summary.get("total_pitches_sent", 0),
                "overall_response_rate": summary.get("overall_response_rate", 0),
                "total_bookings": summary.get("total_bookings", 0),
                "total_responses": summary.get("total_responses", 0),
            })
        except Exception:
            continue

    return trend
