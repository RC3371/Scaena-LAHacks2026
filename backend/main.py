import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routers import profiles, market_research, prospects, pitches, responses, analytics, followups

app = FastAPI(title="Entertainment Booking Automation API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profiles.router)
app.include_router(market_research.router)
app.include_router(prospects.router)
app.include_router(pitches.router)
app.include_router(responses.router)
app.include_router(analytics.router)
app.include_router(followups.router)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "1.0.0"}
