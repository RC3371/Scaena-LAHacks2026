from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from backend.database import get_db
from backend import models, schemas
from backend.services.mongo_store import mirror_agent_event
from backend.websocket_manager import manager
from typing import List
import json

router = APIRouter(tags=["agent_events"])


@router.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


@router.post("/agent-events/broadcast")
async def broadcast_event(event: dict, db: Session = Depends(get_db)):
    await manager.broadcast(event)
    # Persist for /agent-events/recent
    record = models.AgentEvent(
        agent_id=event.get("agent_id", "unknown"),
        event_type=event.get("event_type", "unknown"),
        message=event.get("message", ""),
        entertainer_id=event.get("entertainer_id"),
        target_id=event.get("target_id"),
        conclusion=event.get("conclusion"),
        extra=json.dumps({k: v for k, v in event.items() if k not in (
            "agent_id", "event_type", "message", "entertainer_id", "target_id", "conclusion"
        )}),
    )
    db.add(record)
    db.commit()
    mirror_agent_event(event)
    return {"ok": True}


@router.get("/agent-events/recent", response_model=List[schemas.AgentEventOut])
def recent_events(limit: int = 50, db: Session = Depends(get_db)):
    return (
        db.query(models.AgentEvent)
        .order_by(models.AgentEvent.created_at.desc())
        .limit(limit)
        .all()
    )


@router.get("/agents/status")
def agents_status(db: Session = Depends(get_db)):
    agents = [
        {"agent_id": "agent1", "name": "Market Research"},
        {"agent_id": "agent2", "name": "Pitching"},
        {"agent_id": "agent3", "name": "Tracking & Learning"},
        {"agent_id": "agent4", "name": "Follow-Up & Post-Booking"},
    ]
    result = []
    for a in agents:
        last = (
            db.query(models.AgentEvent)
            .filter(models.AgentEvent.agent_id == a["agent_id"])
            .order_by(models.AgentEvent.created_at.desc())
            .first()
        )
        status = "idle"
        if last:
            if last.event_type == "working":
                status = "working"
            elif last.event_type in ("complete", "insight", "pitch_ready"):
                status = "complete"
            elif last.event_type == "error":
                status = "error"
        result.append({
            "agent_id": a["agent_id"],
            "name": a["name"],
            "status": status,
            "last_event": last.message if last else None,
        })
    return result
