import os
import json
import httpx
from datetime import datetime
from agents.agent_runtime import Agent, Context
from agents.shared_models import (
    MarketResearchResult, LearningInsights, TriggerResearch, ResearchRefinement,
    AGENT2_ADDRESS
)
from agents.research_sources import curated_opportunity_fallback, discover_live_venues, live_sources_configured

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
_api_key = os.getenv("ASI1_API_KEY", "").strip()
_simulation_mode = not _api_key or _api_key in {"placeholder", "your_asi1_api_key_here"}

agent = Agent(
    name="scaena_market_research",
    seed=os.getenv("AGENT1_SEED", "scaena_market_research_seed"),
    port=8001,
)

try:
    from openai import OpenAI
    _llm = OpenAI(
        base_url=os.getenv("ASI1_BASE_URL", "https://api.asi1.ai/v1"),
        api_key=os.getenv("ASI1_API_KEY", "placeholder"),
    )
except Exception:
    _llm = None


def broadcast(event_type: str, message: str, entertainer_id: str = "all", **extra):
    try:
        payload = {"agent_id": "agent1", "event_type": event_type, "message": message, "entertainer_id": entertainer_id, **extra}
        httpx.post(f"{BACKEND_URL}/agent-events/broadcast", json=payload, timeout=5)
    except Exception:
        pass


def _mock_research(entertainer: dict, prior_learning: dict = None, user_instruction: str = "") -> dict:
    etype = entertainer.get("type", "performer")
    artist_name = entertainer.get("name", "the artist")
    location = entertainer.get("location", "Los Angeles, CA")
    followers = entertainer.get("social_followers", 5000)
    exp = entertainer.get("experience_years", 2)
    rate_base = 300 + (exp * 25) + (followers // 500)

    venue_templates = {
        "comedian": [
            {"name": "Comedy Club", "venue_type": "Comedy Club", "typical_pay": f"${rate_base}-{rate_base+150}/show", "fit_score": 0.95, "contact_approach": "Email booking manager", "why_fits": "Core audience of comedy fans", "specific_examples": ["The Comedy Store", "Laugh Factory", "Improv"]},
            {"name": "Corporate Event", "venue_type": "Corporate", "typical_pay": f"${rate_base+200}-{rate_base+500}/show", "fit_score": 0.75, "contact_approach": "LinkedIn + event coordinators", "why_fits": "Companies pay premium for entertainment", "specific_examples": ["Company holiday parties", "Team events"]},
            {"name": "College Campus", "venue_type": "College", "typical_pay": f"${rate_base}-{rate_base+300}/show", "fit_score": 0.85, "contact_approach": "Email student activities board", "why_fits": "Students love relatable humor", "specific_examples": ["UCLA", "USC", "Community colleges"]},
            {"name": "Bar & Brewery", "venue_type": "Bar", "typical_pay": f"${rate_base-100}-{rate_base}/show", "fit_score": 0.70, "contact_approach": "Contact owner directly", "why_fits": "Casual audience, good for brand building", "specific_examples": ["Local craft breweries", "Bar with stage"]},
            {"name": "Festival Stage", "venue_type": "Festival", "typical_pay": f"${rate_base+100}-{rate_base+400}/show", "fit_score": 0.80, "contact_approach": "Submit via festival portal", "why_fits": "Large captive audience", "specific_examples": ["Comedy festivals", "Art festivals"]},
        ],
        "rapper": [
            {"name": "UCLA Campus Events", "venue_type": "College", "typical_pay": f"${rate_base}-{rate_base+250}/show", "fit_score": 0.96, "contact_approach": "Email student activities board", "why_fits": f"{artist_name}'s hip-hop sound fits UCLA's student event crowd, and one packed campus show can move the artist toward a major exposure goal.", "specific_examples": ["Bruin Bash", "UCLA Student Alumni events", "Campus concerts"]},
            {"name": "USC Spring Concert", "venue_type": "College", "typical_pay": f"${rate_base}-{rate_base+250}/show", "fit_score": 0.93, "contact_approach": "Contact student programming board", "why_fits": "USC's concert programming favors energetic emerging acts who can promote hard to students and nearby LA fans.", "specific_examples": ["USC Concerts Committee", "Springfest", "Greek life events"]},
            {"name": "UCSD Sun God Festival", "venue_type": "Festival", "typical_pay": f"${rate_base+75}-{rate_base+400}/show", "fit_score": 0.90, "contact_approach": "Submit EPK through festival application portal", "why_fits": "Sun God is a high-volume student festival, making it a strong single-show exposure play for a growing hip-hop act.", "specific_examples": ["Sun God Festival", "student opener slots", "outdoor hip-hop stages"]},
            {"name": "The Roxy Theatre", "venue_type": "Music Venue", "typical_pay": f"${rate_base-50}-{rate_base+175}/show", "fit_score": 0.89, "contact_approach": "Send EPK and live reel to booking manager", "why_fits": f"The Roxy gives {artist_name} a credible Sunset Strip stage while still matching an emerging-artist price point.", "specific_examples": ["local hip-hop showcases", "support slots", "new artist nights"]},
            {"name": "Bardot Hollywood", "venue_type": "Bar", "typical_pay": f"${rate_base-100}-{rate_base+25}/show", "fit_score": 0.86, "contact_approach": "DM booking manager and follow with email", "why_fits": "Bardot's nightlife crowd overlaps with college-age hip-hop fans and can convert social followers into weekend attendees.", "specific_examples": ["hip-hop nights", "Hollywood bar showcases", "late-night sets"]},
            {"name": "The Troubadour", "venue_type": "Music Venue", "typical_pay": f"${rate_base-25}-{rate_base+250}/show", "fit_score": 0.86, "contact_approach": "Email booking desk with EPK and short reel", "why_fits": "The Troubadour adds industry credibility and gives emerging artists a room where live music fans intentionally discover new acts.", "specific_examples": ["opening slots", "LA showcase bills", "emerging artist nights"]},
            {"name": "Harvard & Stone", "venue_type": "Bar", "typical_pay": f"${rate_base-125}-{rate_base}/show", "fit_score": 0.80, "contact_approach": "Contact owner or talent buyer directly", "why_fits": "Harvard & Stone is a practical bar target for repeat income and late-night crowd building inside an emerging artist's rate range.", "specific_examples": ["East Hollywood sets", "genre crossover nights", "bar residencies"]},
            {"name": "UC Berkeley Student Union", "venue_type": "College", "typical_pay": f"${rate_base}-{rate_base+250}/show", "fit_score": 0.84, "contact_approach": "Reach student union programming by email", "why_fits": "Berkeley's student culture is receptive to independent hip-hop, especially artists with direct campus-friendly messaging.", "specific_examples": ["student union shows", "campus arts events", "welcome week programming"]},
            {"name": "The Echo / Echoplex", "venue_type": "Music Venue", "typical_pay": f"${rate_base-75}-{rate_base+100}/show", "fit_score": 0.83, "contact_approach": "Submit through venue booking form", "why_fits": "Echo Park rooms are strong for LA artists building repeat local fans rather than one-off vanity bookings.", "specific_examples": ["local showcases", "support slots", "indie hip-hop nights"]},
            {"name": "Coachella Emerging Stage", "venue_type": "Festival", "typical_pay": f"${rate_base+150}-{rate_base+650}/show", "fit_score": 0.78, "contact_approach": "Send press kit to talent buyer", "why_fits": "A long-shot festival target, but the exposure upside makes it a useful stretch objective.", "specific_examples": ["emerging artist submissions", "regional buzz slots", "hip-hop daytime stage"]},
        ],
        "speaker": [
            {"name": "Corporate Conference", "venue_type": "Corporate", "typical_pay": f"${rate_base+500}-{rate_base+2000}/show", "fit_score": 0.95, "contact_approach": "Speaker bureau or direct outreach to event organizers", "why_fits": "Highest pay, professional audience", "specific_examples": ["Industry conferences", "TEDx events"]},
            {"name": "University Guest Lecture", "venue_type": "University", "typical_pay": f"${rate_base}-{rate_base+500}/show", "fit_score": 0.85, "contact_approach": "Email department heads", "why_fits": "Builds academic credibility", "specific_examples": ["MBA programs", "Entrepreneurship centers"]},
            {"name": "Podcast", "venue_type": "Media", "typical_pay": f"$0-{rate_base}/show", "fit_score": 0.70, "contact_approach": "Pitch to podcast hosts via email", "why_fits": "Massive reach for thought leaders", "specific_examples": ["Business podcasts", "Industry shows"]},
        ],
        "dj": [
            {"name": "Nightclub Residency", "venue_type": "Nightclub", "typical_pay": f"${rate_base+100}-{rate_base+400}/show", "fit_score": 0.95, "contact_approach": "Contact venue's talent buyer", "why_fits": "Core DJ market, recurring income", "specific_examples": ["Club residencies", "Weekly nights"]},
            {"name": "Wedding", "venue_type": "Wedding", "typical_pay": f"${rate_base+200}-{rate_base+600}/show", "fit_score": 0.85, "contact_approach": "Wedding vendor directories, bridal shows", "why_fits": "Premium private events", "specific_examples": ["Wedding receptions", "Engagement parties"]},
            {"name": "Corporate Event", "venue_type": "Corporate", "typical_pay": f"${rate_base+300}-{rate_base+800}/show", "fit_score": 0.80, "contact_approach": "Event planning companies", "why_fits": "High budgets for entertainment", "specific_examples": ["Holiday parties", "Product launches"]},
            {"name": "Music Festival", "venue_type": "Festival", "typical_pay": f"${rate_base+200}-{rate_base+1000}/show", "fit_score": 0.90, "contact_approach": "Festival booking submissions", "why_fits": "Exposure + premium pay", "specific_examples": ["EDM festivals", "Multi-genre fests"]},
        ],
    }

    venues = venue_templates.get(etype.lower(), venue_templates["rapper"])

    for venue in venues:
        if not venue.get("contact_email"):
            slug = "".join(ch if ch.isalnum() else "-" for ch in venue["name"].lower()).strip("-")
            while "--" in slug:
                slug = slug.replace("--", "-")
            venue["contact_name"] = venue.get("contact_name") or "Booking Team"
            venue["contact_email"] = f"{slug}@example.com"
            venue["source_url"] = venue.get("source_url") or ""

    if prior_learning and prior_learning.get("best_venue_types"):
        best = prior_learning["best_venue_types"]
        venues = sorted(venues, key=lambda v: 1 if v["venue_type"] in best else 0, reverse=True)

    if etype.lower() == "rapper":
        insights_narrative = (
            f"Rappers in {location} are seeing the best early traction from college programming, music venues, bars, and student-heavy festivals. "
            f"With {followers:,} followers and {exp} years performing, {artist_name} should keep pricing near the current target range while prioritizing rooms that can deliver meaningful audience exposure."
        )
    else:
        insights_narrative = (
            f"{etype.capitalize()}s in {location} are seeing strong demand, especially from "
            f"{'corporate clients and festivals' if followers > 10000 else 'local venues and colleges'}. "
            f"With {exp} years of experience, targeting {'premium' if exp > 3 else 'emerging'} venues "
            f"will maximize both exposure and income."
        )

    return {
        "market_rate_low": rate_base - 50,
        "market_rate_high": rate_base + 400,
        "recommended_rate": rate_base + 100,
        "pricing_trend": "rising" if followers > 8000 else "stable",
        "venues": venues[:10],
        "market_insights": insights_narrative,
    }


async def research_for_entertainer(ctx: Context, entertainer: dict):
    eid = entertainer["id"]
    prior_learning = ctx.storage.get("learning_insights") or {}
    prior = prior_learning.get(eid, {})
    user_refinements = ctx.storage.get("user_refinements") or {}
    user_instruction = user_refinements.get(eid, "")
    data = None

    broadcast("working", f"Building a booking-agent opportunity list for {entertainer['name']}...", eid)

    if live_sources_configured():
        broadcast("working", "Searching Gemini-grounded Google results, campus/event pages, Eventbrite, Peerspace, and public social pages...", eid)
        data = discover_live_venues(entertainer, user_instruction)
        if not data:
            broadcast("error", "Live discovery returned no usable results or hit provider quota. Loading agent-curated opportunities.", eid)
            data = curated_opportunity_fallback(entertainer, user_instruction)

    if "data" not in locals() or data is None:
        if _simulation_mode:
            data = _mock_research(entertainer, prior, user_instruction)
        else:
            learning_ctx = ""
            if prior:
                learning_ctx = f"Prior insights: best venues={prior.get('best_venue_types', [])}, best angle={prior.get('best_pitch_angle', '')}, optimal price=${prior.get('optimal_price', 0)}/show. Focus research on these."
            user_ctx = f"\nUser instruction: {user_instruction}" if user_instruction else ""

            prompt = f"""You are replacing the manual research work of a celebrity booking agent.
Research actionable gig opportunities for a {entertainer['type']} ({entertainer.get('genre','')}) in {entertainer.get('location','')}.
Experience: {entertainer.get('experience_years', 2)} years. Following: {entertainer.get('social_followers', 0)}.
{learning_ctx}{user_ctx}

Only return venues, organizations, event series, or buyer surfaces that have a realistic path to booking.
Prioritize buyer path, audience fit, likely rate/exposure value, and the next action Agent 2 should take.

Return ONLY JSON:
{{"market_rate_low": <number>, "market_rate_high": <number>, "recommended_rate": <number>,
"pricing_trend": "rising|stable|falling",
"venues": [{{"name": "<name>", "venue_type": "<type>", "typical_pay": "<$X-Y>", "fit_score": <0.0-1.0>,
"contact_approach": "<specific next action>", "why_fits": "<agent-quality reason>", "specific_examples": ["<source clue>","<buyer path>","<programming fit>"]}}],
"market_insights": "<2-3 sentences>"}}"""
            try:
                resp = _llm.chat.completions.create(
                    model=os.getenv("ASI1_MODEL", "asi1-mini"),
                    messages=[{"role": "system", "content": "Return only valid JSON."}, {"role": "user", "content": prompt}],
                    max_tokens=2000,
                )
                raw = resp.choices[0].message.content.replace("```json", "").replace("```", "").strip()
                data = json.loads(raw)
            except Exception as e:
                ctx.logger.error(f"LLM research failed: {e}")
                data = _mock_research(entertainer, prior, user_instruction)

    try:
        httpx.post(f"{BACKEND_URL}/venues/bulk", json={
            "entertainer_id": eid,
            "venues": data["venues"],
            "market_insights": data.get("market_insights", ""),
            "recommended_rate": data.get("recommended_rate", 350),
        }, timeout=10)
    except Exception as e:
        ctx.logger.error(f"Failed to save venues: {e}")

    broadcast("complete", f"Found {len(data['venues'])} venues. Rate: ${data['recommended_rate']:.0f}/show. Sending to Agent 2.", eid)

    result = MarketResearchResult(
        entertainer_id=eid,
        entertainer_type=entertainer["type"],
        market_rate_low=data["market_rate_low"],
        market_rate_high=data["market_rate_high"],
        recommended_rate=data["recommended_rate"],
        venues=data["venues"],
        market_insights=data.get("market_insights", ""),
        pricing_trend=data.get("pricing_trend", "stable"),
        timestamp=str(datetime.utcnow()),
    )
    await ctx.send(AGENT2_ADDRESS, result)


@agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info(f"Agent 1 (Market Research) started: {agent.address}")
    if not ctx.storage.get("initialized"):
        ctx.storage.set("initialized", True)
        ctx.storage.set("round_number", 1)
        ctx.storage.set("learning_insights", {})


@agent.on_interval(period=604800)
async def run_weekly_research(ctx: Context):
    ctx.logger.info("Running market research cycle...")
    try:
        resp = httpx.get(f"{BACKEND_URL}/entertainers/active", timeout=10)
        entertainers = resp.json()
    except Exception as e:
        ctx.logger.error(f"Failed to fetch entertainers: {e}")
        return
    for ent in entertainers:
        await research_for_entertainer(ctx, ent)


@agent.on_message(model=TriggerResearch)
async def handle_trigger(ctx: Context, sender: str, msg: TriggerResearch):
    ctx.logger.info(f"Manual research triggered for {msg.entertainer_id}")
    try:
        resp = httpx.get(f"{BACKEND_URL}/entertainers/{msg.entertainer_id}", timeout=10)
        ent = resp.json()
        await research_for_entertainer(ctx, ent)
    except Exception as e:
        ctx.logger.error(f"Trigger failed: {e}")


@agent.on_message(model=ResearchRefinement)
async def handle_refinement(ctx: Context, sender: str, msg: ResearchRefinement):
    ctx.logger.info(f"Refinement for {msg.entertainer_id}: {msg.user_instruction}")
    refinements = ctx.storage.get("user_refinements") or {}
    refinements[msg.entertainer_id] = msg.user_instruction
    ctx.storage.set("user_refinements", refinements)
    broadcast("working", f"Re-researching with: {msg.user_instruction}", msg.entertainer_id)
    try:
        resp = httpx.get(f"{BACKEND_URL}/entertainers/{msg.entertainer_id}", timeout=10)
        ent = resp.json()
        await research_for_entertainer(ctx, ent)
    except Exception as e:
        ctx.logger.error(f"Refinement research failed: {e}")


@agent.on_message(model=LearningInsights)
async def receive_learning(ctx: Context, sender: str, msg: LearningInsights):
    ctx.logger.info(f"Received learning for {msg.entertainer_id} round {msg.round_number}")
    insights = ctx.storage.get("learning_insights") or {}
    insights[msg.entertainer_id] = {
        "best_venue_types": msg.best_venue_types,
        "best_pitch_angle": msg.best_pitch_angle,
        "optimal_price": msg.optimal_price,
        "avoid_segments": msg.avoid_segments,
    }
    ctx.storage.set("learning_insights", insights)
