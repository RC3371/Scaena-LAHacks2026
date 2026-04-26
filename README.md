# Scaena OS - Entertainment Booking Automation

AI-powered system that automates client acquisition for entertainment professionals: rappers, musicians, speakers, DJs, and more.

## Quick Start

```bash
# 1. Configure local secrets
cp Scaena/.env.example Scaena/.env

# Optional live market research sources:
# - GEMINI_API_KEY for Gemini Grounding with Google Search
# - GOOGLE_SEARCH_API_KEY + GOOGLE_SEARCH_ENGINE_ID for direct Google/Peerspace/social discovery
# - EVENTBRITE_API_TOKEN for Eventbrite event discovery

# 2. Start everything
cd Scaena && ./start.sh
```

Then open http://localhost:5173 to create an entertainer profile or load the optional demo seed data.

Set `SCAENA_SEED_DEMO=true` only when you intentionally want to load the demo fixture.

## Architecture

```
backend/
  main.py               # FastAPI app
  database.py           # SQLite schema + connection
  models.py             # Pydantic request/response models
  seed_data.py          # Optional demo data fixture
  agents/
    agent1_market_research.py   # Venue discovery + rate analysis
    agent2_pitch_generator.py   # Personalized email generation
    agent3_analytics.py         # Response tracking + insights
    agent4_followup.py          # Follow-up sequencer + objection handling
  routers/
    profiles.py         # Entertainer profile CRUD
    market_research.py  # Agent 1 trigger + results
    prospects.py        # Venue/opportunity management
    pitches.py          # Pitch generation + send tracking
    responses.py        # Response recording + objection handling
    analytics.py        # Agent 3 analysis + trend data
    followups.py        # Agent 4 follow-up management

frontend/
  src/
    pages/
      Onboarding.jsx    # 3-step profile setup
      Dashboard.jsx     # Overview + 4-agent pipeline status
      MarketResearch.jsx  # Agent 1 results
      Prospects.jsx     # Venue pipeline kanban
      Pitches.jsx       # Generate, review, send + record responses
      Analytics.jsx     # Charts + AI strategy recommendations
      FollowUps.jsx     # Follow-up queue management
```

## The 4-Agent Feedback Loop

1. **Agent 1 (Market Research)** — Claude researches market rates + discovers 30 venues tailored to the entertainer's type and location
2. **Agent 2 (Pitch Generator)** — Claude writes personalized pitches for each selected venue, referencing their vibe and recent bookings
3. **Agent 3 (Analytics)** — Analyzes response rates by venue type, identifies best-performing pitch angles, generates AI strategy recommendations
4. **Agent 4 (Follow-Up Engine)** — Schedules Day 3/7/14 follow-ups for non-responders, generates objection counter-offers

Each round, Agent 3's insights feed back into Agents 1 and 2, improving targeting and conversion.

## Tech Stack

- **Backend:** FastAPI + SQLite + Anthropic Python SDK (claude-sonnet-4-6)
- **Frontend:** React 18 + Vite + Tailwind CSS + Recharts
- **No external databases** — fully local SQLite

## API Docs

Swagger UI available at http://localhost:8000/docs after starting the backend.
