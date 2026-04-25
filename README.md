# GigAI — Entertainment Booking Automation

AI-powered system that automates client acquisition for entertainment professionals: comedians, rappers, speakers, DJs, and more.

## Quick Start

```bash
# 1. Add your Anthropic API key
echo "ANTHROPIC_API_KEY=your_key_here" > backend/.env

# 2. Start everything (installs deps + seeds demo data automatically)
./start.sh
```

Then open http://localhost:5173 and click **"Use demo profile"** to see Alex Rivera's (comedian) pre-seeded 3-week pipeline.

## Architecture

```
backend/
  main.py               # FastAPI app
  database.py           # SQLite schema + connection
  models.py             # Pydantic request/response models
  seed_data.py          # Demo data (Alex Rivera - comedian)
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
