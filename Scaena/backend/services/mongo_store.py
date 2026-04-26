import os
from datetime import datetime
from typing import Any

from backend.mongo import _mongo_client_options, get_db


def _mongo_client():
    uri = (os.getenv("MONGODB_URI") or os.getenv("MONGO_URI") or "").strip()
    if not uri:
        return None
    try:
        from pymongo import MongoClient
    except ImportError:
        return None
    try:
        return MongoClient(uri, **_mongo_client_options())
    except Exception:
        return None


def _database():
    db = get_db()
    return db


def mongo_enabled() -> bool:
    return _database() is not None


def mongo_health_detail() -> str:
    uri = (os.getenv("MONGODB_URI") or os.getenv("MONGO_URI") or "").strip()
    if not uri:
        return "not configured"
    try:
        from pymongo import MongoClient
    except ImportError:
        return "MONGODB_URI set but pymongo is not installed"
    try:
        MongoClient(uri, **_mongo_client_options()).admin.command("ping")
        return f"connected to {os.getenv('MONGODB_DB_NAME') or os.getenv('MONGODB_DB') or 'scaena'}"
    except Exception:
        return "configured but not reachable"


def _clean_doc(value: Any) -> Any:
    if isinstance(value, datetime):
        return value
    if isinstance(value, dict):
        return {str(k): _clean_doc(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_clean_doc(item) for item in value]
    if isinstance(value, tuple):
        return [_clean_doc(item) for item in value]
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            return str(value)
    return value


def mirror_agent_event(event: dict):
    db = _database()
    if db is None:
        return
    doc = _clean_doc({
        **event,
        "mirrored_at": datetime.utcnow(),
    })
    try:
        db.agent_events.insert_one(doc)
    except Exception:
        return


def mirror_venues(entertainer_id: str, venues: list[dict], source: str = "market_research"):
    db = _database()
    if db is None:
        return
    now = datetime.utcnow()
    docs = []
    for venue in venues:
        docs.append(_clean_doc({
            **venue,
            "entertainer_id": entertainer_id,
            "source": source,
            "mirrored_at": now,
        }))
    if not docs:
        return
    try:
        log_collection = db.venues
        opportunity_collection = db.venue_opportunities
        for doc in docs:
            log_collection.insert_one({
                "entertainer_id": entertainer_id,
                "venue_name": doc.get("name"),
                "fit_score": doc.get("fit_score"),
                "source": source,
                "discovered_at": now,
            })
            key = {
                "entertainer_id": entertainer_id,
                "name": doc.get("name"),
                "source_url": doc.get("source_url"),
            }
            opportunity_collection.update_one(key, {"$set": doc, "$setOnInsert": {"created_at": now}}, upsert=True)
    except Exception:
        return


def mirror_pitch_sent(pitch: Any, recipient: str | None = None, dry_run: bool = False, source: str = "gmail"):
    db = _database()
    if db is None:
        return

    sent_at = getattr(pitch, "sent_at", None) or datetime.utcnow()
    doc = _clean_doc({
        "pitch_id": getattr(pitch, "id", None),
        "entertainer_id": getattr(pitch, "entertainer_id", None),
        "venue_name": getattr(pitch, "venue_name", None),
        "recipient_email": recipient or getattr(pitch, "recipient_email", None),
        "pitch_subject": getattr(pitch, "pitch_subject", None),
        "pitch_body": getattr(pitch, "pitch_body", None),
        "status": "sent",
        "dry_run": dry_run,
        "source": source,
        "gmail_message_id": getattr(pitch, "gmail_message_id", None),
        "gmail_thread_id": getattr(pitch, "gmail_thread_id", None),
        "sent_at": sent_at,
        "mirrored_at": datetime.utcnow(),
    })

    try:
        db.pitches.insert_one(doc)
    except Exception:
        return
