import os
import json
import uuid
import httpx
from datetime import datetime
from agents.agent_runtime import Agent, Context
from agents.shared_models import (
    MarketResearchResult, OutreachBatchSent, TargetStrategyUpdate,
    AGENT3_ADDRESS
)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
_api_key = os.getenv("ASI1_API_KEY", "").strip()
_simulation_mode = not _api_key or _api_key in {"placeholder", "your_asi1_api_key_here"}

agent = Agent(
    name="scaena_outreach_pitching",
    seed=os.getenv("AGENT2_SEED", "scaena_pitching_seed"),
    port=8002,
)

try:
    from openai import OpenAI
    _llm = OpenAI(
        base_url=os.getenv("ASI1_BASE_URL", "https://api.asi1.ai/v1"),
        api_key=os.getenv("ASI1_API_KEY", "placeholder"),
    )
except Exception:
    _llm = None


def broadcast(event_type: str, message: str, entertainer_id: str, **extra):
    try:
        httpx.post(f"{BACKEND_URL}/agent-events/broadcast", json={
            "agent_id": "agent2", "event_type": event_type,
            "message": message, "entertainer_id": entertainer_id, **extra
        }, timeout=5)
    except Exception:
        pass


def _mock_pitch(entertainer: dict, venue: dict, rate: float) -> dict:
    import hashlib
    name = entertainer.get("name", "The Artist")
    etype = entertainer.get("type", "performer")
    genre = entertainer.get("genre", "")
    exp = entertainer.get("experience_years", 2)
    followers = entertainer.get("social_followers", 5000)
    location = entertainer.get("location", "LA")
    venue_name = venue.get("name", "your venue")
    venue_type = (venue.get("venue_type") or "").lower()
    why_fits = (venue.get("why_fits") or "").strip()
    venue_context = f"\n\nI noticed {why_fits.rstrip('.')}. That is exactly the kind of fit I am looking for right now." if why_fits else ""

    idx = int(hashlib.md5(f"{name}{venue_name}".encode()).hexdigest(), 16) % 3

    # Human-tone, venue-type-specific templates for rappers
    if etype.lower() == "rapper":
        if "college" in venue_type or "university" in venue_type:
            subjects = [
                f"Performance Booking — {name} for {venue_name}",
                f"{name} | Hip-Hop Act for {venue_name}",
                f"Rapper Available for {venue_name} — {name}",
            ]
            bodies = [
                f"Hey {venue_name} team,\n\nI'm {name}, a rapper out of {location} making high-energy hip-hop for college crowds. I've been performing for {exp} years and have {followers:,} followers across socials.{venue_context}\n\nI can bring a tight 30-minute set, promote the event hard, and keep the show student-friendly without losing the energy. My usual rate is ${rate:.0f}/show, and I am flexible if there is a student board budget to work around.\n\nCould I send over a reel for an upcoming campus slot?\n\n{name}",
                f"What's up {venue_name},\n\nI'm {name}, an LA hip-hop artist building toward more campus shows this year. The goal is simple: play rooms where students actually discover new artists, not just background sets.{venue_context}\n\nI bring a crowd-interactive set, clean versions when needed, and promo support to {followers:,} followers. Rate is ${rate:.0f}/show.\n\nIs there a programming slot this semester where I might make sense?\n\n{name}",
                f"Hi {venue_name} team,\n\nI'm reaching out because your campus audience feels aligned with what I do. I'm {name}, a {genre or 'hip-hop'} artist from {location} with {exp} years of live experience and {followers:,} social followers.{venue_context}\n\nMy set is built for student energy: hooks, call-and-response moments, and an easy 30-45 minute format. Rate is ${rate:.0f}/show.\n\nHappy to send music and a short performance reel.\n\n{name}",
            ]
        elif "festival" in venue_type:
            subjects = [
                f"{name} — Festival Performance Inquiry",
                f"Booking Request: {name} for {venue_name}",
                f"Hip-Hop Artist Submission — {name} | {venue_name}",
            ]
            bodies = [
                f"Hi {venue_name} team,\n\nI'm {name}, a rapper from {location} submitting for an emerging hip-hop slot. I have {followers:,} followers, {exp} years of live experience, and a set that is built to catch people walking between stages.{venue_context}\n\nI can do 20, 30, or 45 minutes, push the appearance across Instagram/TikTok/YouTube, and keep the production simple. Rate is ${rate:.0f}/show depending on slot.\n\nCan I send over my EPK and reel?\n\n{name}",
                f"Hey {venue_name},\n\nI'm applying for a performance slot as {name}, an independent hip-hop artist from {location}. I'm specifically chasing festival looks because they line up with my goal of reaching 1000+ new people this year.{venue_context}\n\nThe live set is high-momentum, crowd-facing, and easy to drop into a showcase lineup. My current rate is ${rate:.0f}, flexible by stage and set length.\n\nWould love to be considered.\n\n{name}",
                f"Hello {venue_name} booking team,\n\nI'm {name}, a {genre or 'hip-hop'} artist from {location}. I have {followers:,} social followers and a live show shaped for festival crowds: quick hooks, strong transitions, and direct audience engagement.{venue_context}\n\nI am available for opener, showcase, or emerging-stage slots. Rate is ${rate:.0f}/show, and I can send a clean EPK today.\n\nThanks for considering it,\n{name}",
            ]
        elif "bar" in venue_type or "nightlife" in venue_type or "nightclub" in venue_type:
            subjects = [
                f"Booking Inquiry — {name} at {venue_name}",
                f"{name} | Looking to Book a Night at {venue_name}",
                f"Hip-Hop Night Booking — {name}",
            ]
            bodies = [
                f"Hey {venue_name},\n\nI'm {name}, a rapper from {location}, and I am looking for bar rooms where a hip-hop set can actually lift the night instead of feeling tacked on.{venue_context}\n\nI have {followers:,} followers, promote every booking, and can bring a 25-35 minute set that works before a DJ, between acts, or as a feature slot. Rate is around ${rate:.0f}, flexible by night.\n\nCould we make a date work?\n\n{name}",
                f"Hi {venue_name} team,\n\nThe room feels right for what I do, so I wanted to reach out directly. I'm {name}, {genre or 'hip-hop'} out of {location}, with {exp} years performing and a growing college-age following.{venue_context}\n\nI can help draw, keep the energy up, and make the promo easy for your team. Rate is ${rate:.0f}/night.\n\nOpen to trying a weekend or showcase slot?\n\n{name}",
                f"What's good {venue_name},\n\nI'm {name}, an LA rapper booking bars and music rooms in the $300-400 range. I am trying to stack consistent shows that build real audience, and your crowd feels like a strong match.{venue_context}\n\nI bring a tight live set, social promo to {followers:,} followers, and a flexible format. Let me know if you have a date that needs hip-hop energy.\n\n{name}",
            ]
        else:  # music venue / generic
            subjects = [
                f"Performance Booking — {name} at {venue_name}",
                f"{name} — Available for {venue_name}",
                f"Rapper Booking Request: {name} | {venue_name}",
            ]
            bodies = [
                f"Hi {venue_name} booking team,\n\nI'm {name}, an independent rapper from {location}. I am reaching out because your stage feels like the right next step for my live show.{venue_context}\n\nI bring a polished 30-45 minute set, promote to {followers:,} followers, and keep the ask straightforward: ${rate:.0f}/show, flexible if it helps build the bill.\n\nCould I send my reel and a few date options?\n\n{name}",
                f"Hey {venue_name},\n\n{name} here, hip-hop out of {location}. I've spent {exp} years building a live set that works in real music rooms, not just online clips.{venue_context}\n\nThe show is high-energy, easy to slot with other local acts, and backed by promo to {followers:,} followers. Rate is ${rate:.0f}, but I care most about finding the right bill.\n\nWorth a quick conversation?\n\n{name}",
                f"Hi there,\n\nI'm reaching out about booking {venue_name}. I'm {name}, a {genre or 'hip-hop'} artist from {location}, focused on college campuses, music venues, festivals, and bars this year.{venue_context}\n\nI do tight 30-45 minute sets with strong stage presence and active pre-show promo. Rate is ${rate:.0f}/show.\n\nLet me know if I should send over the EPK.\n\n{name}",
            ]
    else:
        # Generic fallback for non-rappers
        subjects = [
            f"Booking Inquiry — {name} ({etype.capitalize()}) for {venue_name}",
            f"{name} — Available for {venue_name} Bookings",
            f"Performance Opportunity: {name} at {venue_name}",
        ]
        bodies = [
            f"Hi,\n\nI'm {name}, a {genre} {etype} based in {location} with {exp} years performing and {followers:,} social followers.\n\nI'd love to bring my show to {venue_name}. My rate is ${rate:.0f}/show — happy to discuss based on your budget.\n\nAvailable most weekends. Worth a quick call?\n\nBest,\n{name}",
            f"Hello,\n\nYour {venue_name} programming caught my eye — I think my {genre} {etype} act would resonate perfectly with your crowd.\n\nQuick pitch: {name}, {exp} years performing, {followers:,} followers. Looking to book at ${rate:.0f}/show.\n\n— {name}",
            f"Hi there,\n\nI'm {name} — {etype} known for {genre.lower()} with {followers:,} followers and {exp} years on stage. I'd love to perform at {venue_name}.\n\nRate: ${rate:.0f}/show.\n\nThanks,\n{name}",
        ]

    return {"subject": subjects[idx], "body": bodies[idx]}


@agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info(f"Agent 2 (Pitching) started: {agent.address}")


@agent.on_message(model=MarketResearchResult)
async def generate_pitches(ctx: Context, sender: str, msg: MarketResearchResult):
    ctx.logger.info(f"Generating pitches for {msg.entertainer_id} ({len(msg.venues)} venues)")
    broadcast("working", f"Generating personalized pitches for {len(msg.venues)} venues...", msg.entertainer_id)

    try:
        resp = httpx.get(f"{BACKEND_URL}/entertainers/{msg.entertainer_id}", timeout=10)
        entertainer = resp.json()
    except Exception as e:
        ctx.logger.error(f"Failed to fetch entertainer: {e}")
        return

    outreach_mode = entertainer.get("outreach_mode", "manual_approve")
    batch_id = str(uuid.uuid4())
    pitch_ids = []

    for venue in msg.venues[:15]:
        broadcast("pitch_generating", f"Writing pitch for {venue['name']}...", msg.entertainer_id, target=venue["name"])

        if _simulation_mode:
            pitch = _mock_pitch(entertainer, venue, msg.recommended_rate)
        else:
            prompt = f"""Write a personalized booking pitch email for:
Entertainer: {entertainer['name']} ({entertainer['type']}, {entertainer.get('genre','')})
Experience: {entertainer.get('experience_years',2)} yrs, {entertainer.get('social_followers',0)} followers
Rate: ${msg.recommended_rate}/show

Venue: {venue['name']} ({venue.get('venue_type','')})
Why fits: {venue.get('why_fits','')}
Examples: {venue.get('specific_examples',[])}

Short (under 150 words), specific, human, confident. Return ONLY JSON: {{"subject":"...","body":"..."}}"""
            try:
                resp_llm = _llm.chat.completions.create(
                    model=os.getenv("ASI1_MODEL", "asi1-mini"),
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=600,
                )
                raw = resp_llm.choices[0].message.content.replace("```json", "").replace("```", "").strip()
                pitch = json.loads(raw)
            except Exception as e:
                ctx.logger.error(f"Pitch gen failed for {venue['name']}: {e}")
                pitch = _mock_pitch(entertainer, venue, msg.recommended_rate)

        status = "sent" if outreach_mode == "auto_pitch" else "draft"
        try:
            resp = httpx.post(f"{BACKEND_URL}/outreach/pitch", json={
                "entertainer_id": msg.entertainer_id,
                "batch_id": batch_id,
                "venue_name": venue["name"],
                "entertainer_type": msg.entertainer_type,
                "recipient_email": venue.get("contact_email"),
                "venue_contact_approach": venue.get("contact_approach", ""),
                "pitch_subject": pitch["subject"],
                "pitch_body": pitch["body"],
                "proposed_rate": msg.recommended_rate,
                "status": status,
            }, timeout=10)
            pitch_id = resp.json().get("pitch_id", "")
            pitch_ids.append(pitch_id)
            broadcast("pitch_ready", f"Pitch ready for {venue['name']} — {status}", msg.entertainer_id, target=venue["name"], pitch_id=pitch_id, status=status)
        except Exception as e:
            ctx.logger.error(f"Failed to save pitch: {e}")

    broadcast("complete", f"{len(pitch_ids)} pitches generated (mode: {outreach_mode})", msg.entertainer_id)

    await ctx.send(AGENT3_ADDRESS, OutreachBatchSent(
        entertainer_id=msg.entertainer_id,
        batch_id=batch_id,
        pitches_sent=len(pitch_ids),
        venue_ids=pitch_ids,
        timestamp=str(datetime.utcnow()),
    ))


@agent.on_message(model=TargetStrategyUpdate)
async def handle_strategy_update(ctx: Context, sender: str, msg: TargetStrategyUpdate):
    ctx.logger.info(f"Strategy update for {msg.target_id}")
    broadcast("working", f"Rewriting pitch: {msg.strategy_instruction}", msg.entertainer_id, target_id=msg.target_id)

    try:
        resp_pitch = httpx.get(f"{BACKEND_URL}/outreach/pitch-by-target/{msg.target_id}", timeout=10)
        pitch_data = resp_pitch.json()
        resp_ent = httpx.get(f"{BACKEND_URL}/entertainers/{msg.entertainer_id}", timeout=10)
        entertainer = resp_ent.json()
    except Exception as e:
        ctx.logger.error(f"Failed to fetch data for strategy update: {e}")
        return

    if _simulation_mode:
        new_pitch = {
            "subject": f"[Updated] {pitch_data.get('pitch_subject', 'Booking Inquiry')}",
            "body": f"{pitch_data.get('pitch_body', '')}\n\nP.S. {msg.strategy_instruction}",
        }
    else:
        rewrite = f"""Rewrite this pitch based on: {msg.strategy_instruction}

Original subject: {pitch_data.get('pitch_subject','')}
Original body: {pitch_data.get('pitch_body','')}
Entertainer: {entertainer['name']} ({entertainer['type']})
Venue: {pitch_data.get('venue_name','')}

Under 150 words. Return ONLY JSON: {{"subject":"...","body":"..."}}"""
        try:
            resp_llm = _llm.chat.completions.create(
                model=os.getenv("ASI1_MODEL", "asi1-mini"),
                messages=[{"role": "user", "content": rewrite}],
                max_tokens=500,
            )
            raw = resp_llm.choices[0].message.content.replace("```json", "").replace("```", "").strip()
            new_pitch = json.loads(raw)
        except Exception as e:
            ctx.logger.error(f"Rewrite failed: {e}")
            return

    try:
        httpx.patch(f"{BACKEND_URL}/outreach/pitch/{pitch_data['id']}", json={
            "pitch_subject": new_pitch["subject"],
            "pitch_body": new_pitch["body"],
            "strategy_note": msg.strategy_instruction,
        }, timeout=10)
        broadcast("pitch_rewritten", f"Pitch for {pitch_data.get('venue_name')} rewritten.", msg.entertainer_id, target_id=msg.target_id)
    except Exception as e:
        ctx.logger.error(f"Failed to save rewrite: {e}")
