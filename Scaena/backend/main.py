import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import init_db
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


@app.on_event("startup")
def on_startup():
    init_db()
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
