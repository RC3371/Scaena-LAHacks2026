import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import init_db
from backend.mongo import get_db as get_mongo_db
from backend.routers import entertainers, venues, outreach, conversations, analytics, agent_events, bookings, gmail
from config_health import print_config_health

app = FastAPI(title="Scaena API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _mongo_health() -> dict:
    db = get_mongo_db()
    if db is None:
        return {"connected": False, "mongo": None}
    try:
        db.client.admin.command("ping")
    except Exception:
        return {"connected": False, "mongo": None}
    return {"connected": True, "mongo": db.name}


@app.on_event("startup")
def on_startup():
    init_db()
    mongo = _mongo_health()
    print(f"MongoDB connected: {mongo['mongo'] if mongo['connected'] else 'not reachable'}", flush=True)
    print_config_health("backend")


app.include_router(entertainers.router)
app.include_router(venues.router)
app.include_router(outreach.router)
app.include_router(conversations.router)
app.include_router(analytics.router)
app.include_router(agent_events.router)
app.include_router(bookings.router)
app.include_router(gmail.router)


@app.get("/")
def root():
    return {"status": "Scaena API running"}


@app.get("/api/health")
def health():
    mongo = _mongo_health()
    return {
        "status": "ok",
        "version": "1.0.0",
        "mongo": mongo["mongo"],
        "mongo_connected": mongo["connected"],
    }
