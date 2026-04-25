import json
from fastapi import APIRouter, HTTPException, BackgroundTasks
from models import MarketResearchRequest
from database import get_db, row_to_dict, rows_to_list
from agents.agent1_market_research import run_market_research

router = APIRouter(prefix="/api/market-research", tags=["market-research"])


@router.post("/run")
def trigger_market_research(data: MarketResearchRequest):
    with get_db() as conn:
        profile = row_to_dict(conn.execute("SELECT * FROM profiles WHERE id = ?", (data.profile_id,)).fetchone())
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    research_data = run_market_research(profile)

    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO market_research (profile_id, research_data) VALUES (?, ?)",
            (data.profile_id, json.dumps(research_data)),
        )
        research_id = cursor.lastrowid

        discovered = research_data.get("discovered_prospects", [])
        prospect_ids = []
        for p in discovered:
            c = conn.execute(
                """INSERT INTO prospects (profile_id, name, type, location, contact_email, contact_name,
                   typical_pay_min, typical_pay_max, notes, source)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'agent1')""",
                (data.profile_id, p.get("name"), p.get("type"), p.get("location"),
                 p.get("contact_email"), p.get("contact_name"),
                 p.get("typical_pay_min", 0), p.get("typical_pay_max", 0), p.get("notes")),
            )
            prospect_ids.append(c.lastrowid)

    return {
        "research_id": research_id,
        "profile_id": data.profile_id,
        "prospects_discovered": len(discovered),
        "prospect_ids": prospect_ids,
        "data": research_data,
    }


@router.get("/{profile_id}")
def get_latest_research(profile_id: int):
    with get_db() as conn:
        row = row_to_dict(conn.execute(
            "SELECT * FROM market_research WHERE profile_id = ? ORDER BY created_at DESC LIMIT 1",
            (profile_id,)
        ).fetchone())
    if not row:
        raise HTTPException(status_code=404, detail="No research found for this profile")
    row["data"] = json.loads(row["research_data"])
    del row["research_data"]
    return row


@router.get("/{profile_id}/history")
def get_research_history(profile_id: int):
    with get_db() as conn:
        rows = rows_to_list(conn.execute(
            "SELECT id, profile_id, created_at FROM market_research WHERE profile_id = ? ORDER BY created_at DESC",
            (profile_id,)
        ).fetchall())
    return rows
