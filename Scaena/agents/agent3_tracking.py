import os
import json
import httpx
from datetime import datetime
from agents.agent_runtime import Agent, Context
from agents.shared_models import (
    OutreachBatchSent, FollowUpEngagement, BookingConversationUpdate,
    LearningInsights, TriggerResearch, TargetReply,
    AGENT1_ADDRESS
)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
_api_key = os.getenv("ASI1_API_KEY", "").strip()
_simulation_mode = not _api_key or _api_key in {"placeholder", "your_asi1_api_key_here"}

agent = Agent(
    name="scaena_analytics_learning",
    seed=os.getenv("AGENT3_SEED", "scaena_tracking_seed"),
    port=8003,
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
        httpx.post(f"{BACKEND_URL}/agent-events/broadcast", json={
            "agent_id": "agent3", "event_type": event_type,
            "message": message, "entertainer_id": entertainer_id, **extra
        }, timeout=5)
    except Exception:
        pass


def broadcast_thinking(step: str, conclusion: str, entertainer_id: str, target_id: str = None):
    try:
        httpx.post(f"{BACKEND_URL}/agent-events/broadcast", json={
            "agent_id": "agent3", "event_type": "thinking",
            "message": step, "conclusion": conclusion,
            "entertainer_id": entertainer_id, "target_id": target_id,
        }, timeout=5)
    except Exception:
        pass


def _mock_conversation_analysis(reply_body: str, venue_name: str) -> dict:
    reply_lower = reply_body.lower()
    is_positive = any(w in reply_lower for w in ["interested", "love to", "sounds good", "available", "rate", "date", "book"])
    is_negative = any(w in reply_lower for w in ["not interested", "no thanks", "full", "budget", "pass", "decline"])
    is_question = "?" in reply_body

    if is_positive:
        interest = "high"
        likelihood = 7.5
        worked = "Personalized approach referencing the venue's audience resonated."
        next_action = "Send availability and propose 2-3 specific dates with logistics."
    elif is_negative:
        interest = "low"
        likelihood = 1.5
        worked = "Made it through to a response, venue at least engaged with the pitch."
        next_action = "Log as declined. Re-engage in 3 months with a seasonal hook."
    elif is_question:
        interest = "medium"
        likelihood = 5.5
        worked = "Subject line drove opens; question suggests genuine consideration."
        next_action = "Answer their question directly and include social proof (reel, past shows)."
    else:
        interest = "medium"
        likelihood = 4.0
        worked = "Pitch generated a response, tone was non-threatening enough to get a reply."
        next_action = "Follow up with a value-add: performance reel or recent press mention."

    return {
        "interest_level": interest,
        "signals": [
            f"Reply received from {venue_name}",
            "Positive language detected" if is_positive else "Neutral/negative tone",
        ],
        "what_worked": worked,
        "what_to_do_next": next_action,
        "conversion_likelihood": likelihood,
        "thinking_steps": [
            {"step": f"Reading reply from {venue_name}...", "conclusion": f"Tone is {'positive' if is_positive else 'cautious' if is_question else 'negative'}"},
            {"step": "Checking for buying signals...", "conclusion": f"Interest level: {interest}"},
            {"step": "Determining recommended action...", "conclusion": next_action},
        ],
    }


def _mock_insights(summary: dict, entertainer_id: str) -> dict:
    by_venue = summary.get("by_venue_type", {})
    best_venues = sorted(by_venue.keys(), key=lambda k: by_venue[k].get("responded", 0) / max(by_venue[k].get("sent", 1), 1), reverse=True)[:3]
    avoid = [k for k in by_venue if by_venue[k].get("responded", 0) == 0 and by_venue[k].get("sent", 0) > 1]
    avg_rate = summary.get("price_data", {}).get("avg_proposed", 350)
    rate = summary.get("response_rate", 0.0)

    return {
        "best_venue_types": best_venues or ["College", "Music Venue", "Festival", "Bar"],
        "avoid_segments": avoid or [],
        "best_pitch_angle": "Video proof + audience fit specificity" if rate > 0.4 else "Social proof + recent show references",
        "optimal_price": avg_rate * 1.1,
        "insights_narrative": (
            f"Response rate is {rate*100:.1f}%. "
            f"{'Strong performance, maintain current strategy.' if rate > 0.4 else 'Below target, shift pitch angle and venue mix.'} "
            f"{'Best venues: ' + ', '.join(best_venues) + '.' if best_venues else ''}"
        ),
        "thinking_steps": [
            {"step": "Scanning response rates by venue type...", "conclusion": f"Top performers: {', '.join(best_venues) if best_venues else 'gathering data'}"},
            {"step": "Analyzing pitch effectiveness...", "conclusion": f"Overall response rate: {rate*100:.1f}%"},
            {"step": "Identifying optimization opportunities...", "conclusion": "Insights sent to Agent 1 for next research round"},
        ],
    }


@agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info(f"Agent 3 (Tracking & Learning) started: {agent.address}")
    if not ctx.storage.get("initialized"):
        ctx.storage.set("initialized", True)
        ctx.storage.set("round_tracker", {})


@agent.on_message(model=OutreachBatchSent)
async def track_batch(ctx: Context, sender: str, msg: OutreachBatchSent):
    ctx.logger.info(f"Tracking batch {msg.batch_id}")
    try:
        httpx.post(f"{BACKEND_URL}/outreach/batch", json={
            "entertainer_id": msg.entertainer_id,
            "batch_id": msg.batch_id,
            "pitches_sent": msg.pitches_sent,
            "timestamp": msg.timestamp,
        }, timeout=10)
    except Exception as e:
        ctx.logger.error(f"Batch log failed: {e}")


@agent.on_message(model=TargetReply)
async def analyze_reply(ctx: Context, sender: str, msg: TargetReply):
    ctx.logger.info(f"Analyzing reply from {msg.target_id}")
    broadcast("working", "Analyzing conversation...", msg.entertainer_id, target_id=msg.target_id)

    try:
        resp = httpx.get(f"{BACKEND_URL}/conversations/{msg.target_id}", timeout=10)
        conversation = resp.json()
    except Exception as e:
        ctx.logger.error(f"Failed to fetch conversation: {e}")
        return

    venue_name = conversation.get("venue_name", "venue")
    broadcast_thinking(f"Reading reply from {venue_name}...", None, msg.entertainer_id, msg.target_id)

    if _simulation_mode:
        analysis = _mock_conversation_analysis(msg.reply_body, venue_name)
    else:
        prompt = f"""Analyze this conversation between an entertainer and a venue.

Pitch sent: {conversation.get('initial_pitch', '')}
Venue reply: {msg.reply_body}
Messages: {json.dumps(conversation.get('messages', [])[:5], indent=2)}

Return ONLY JSON:
{{"interest_level":"high|medium|low|none","signals":["<s1>","<s2>"],"what_worked":"<text>",
"what_to_do_next":"<specific action>","conversion_likelihood":<0-10>,
"thinking_steps":[{{"step":"<obs>","conclusion":"<meaning>"}}]}}"""
        try:
            resp_llm = _llm.chat.completions.create(
                model=os.getenv("ASI1_MODEL", "asi1-mini"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
            )
            raw = resp_llm.choices[0].message.content.replace("```json", "").replace("```", "").strip()
            analysis = json.loads(raw)
        except Exception as e:
            ctx.logger.error(f"Analysis LLM failed: {e}")
            analysis = _mock_conversation_analysis(msg.reply_body, venue_name)

    for thought in analysis.get("thinking_steps", []):
        broadcast_thinking(thought["step"], thought.get("conclusion"), msg.entertainer_id, msg.target_id)

    try:
        httpx.post(f"{BACKEND_URL}/conversations/analysis", json={
            "target_id": msg.target_id,
            "entertainer_id": msg.entertainer_id,
            "interest_level": analysis["interest_level"],
            "signals": analysis["signals"],
            "what_worked": analysis["what_worked"],
            "what_to_do_next": analysis["what_to_do_next"],
            "conversion_likelihood": analysis["conversion_likelihood"],
        }, timeout=10)
    except Exception as e:
        ctx.logger.error(f"Failed to save analysis: {e}")

    broadcast("insight", analysis["what_worked"], msg.entertainer_id,
              target_id=msg.target_id, interest_level=analysis["interest_level"],
              next_action=analysis["what_to_do_next"], conversion_likelihood=analysis["conversion_likelihood"])


@agent.on_message(model=FollowUpEngagement)
async def track_followup(ctx: Context, sender: str, msg: FollowUpEngagement):
    try:
        httpx.post(f"{BACKEND_URL}/outreach/followup-result", json={
            "entertainer_id": msg.entertainer_id,
            "venue_id": msg.venue_id,
            "followup_number": msg.followup_number,
            "response_received": msg.response_received,
            "response_type": msg.response_type,
            "timestamp": msg.timestamp,
        }, timeout=10)
    except Exception as e:
        ctx.logger.error(f"Follow-up result log failed: {e}")
    await maybe_generate_insights(ctx, msg.entertainer_id)


@agent.on_message(model=BookingConversationUpdate)
async def track_booking(ctx: Context, sender: str, msg: BookingConversationUpdate):
    ctx.logger.info(f"Booking update: {msg.target_id} stage={msg.conversation_stage}")
    broadcast("working", f"Analyzing post-booking stage: {msg.conversation_stage}", msg.entertainer_id, target_id=msg.target_id)
    try:
        httpx.post(f"{BACKEND_URL}/conversations/booking-update", json={
            "target_id": msg.target_id,
            "entertainer_id": msg.entertainer_id,
            "booking_id": msg.booking_id,
            "message_sent": msg.message_sent,
            "response_received": msg.response_received,
            "conversation_stage": msg.conversation_stage,
            "timestamp": msg.timestamp,
        }, timeout=10)
    except Exception as e:
        ctx.logger.error(f"Booking update failed: {e}")
    await maybe_generate_insights(ctx, msg.entertainer_id)


@agent.on_interval(period=259200)
async def periodic_analysis(ctx: Context):
    ctx.logger.info("Running periodic pattern analysis...")
    broadcast("working", "Running periodic analysis across all conversations...", "all")
    try:
        resp = httpx.get(f"{BACKEND_URL}/entertainers/active", timeout=10)
        entertainers = resp.json()
        for ent in entertainers:
            await maybe_generate_insights(ctx, ent["id"])
    except Exception as e:
        ctx.logger.error(f"Periodic analysis failed: {e}")


async def maybe_generate_insights(ctx: Context, entertainer_id: str):
    try:
        resp = httpx.get(f"{BACKEND_URL}/analytics/summary/{entertainer_id}", timeout=10)
        summary = resp.json()
    except Exception as e:
        ctx.logger.error(f"Failed to fetch summary: {e}")
        return

    if summary.get("total_responses", 0) < 3:
        return

    broadcast_thinking("Scanning response patterns...", None, entertainer_id)

    if _simulation_mode:
        data = _mock_insights(summary, entertainer_id)
    else:
        prompt = f"""Analyze outreach performance:
Total pitches: {summary['total_pitches']}, responses: {summary['total_responses']}, rate: {summary['response_rate']*100:.1f}%
Accepted: {summary['accepted']}, rejected: {summary['rejected']}
By venue: {json.dumps(summary.get('by_venue_type', {}), indent=2)}
Follow-up rates: fu1={summary['followup1_rate']*100:.1f}%, fu2={summary['followup2_rate']*100:.1f}%

Return ONLY JSON:
{{"best_venue_types":["<t1>"],"avoid_segments":["<t>"],"best_pitch_angle":"<desc>",
"optimal_price":<number>,"insights_narrative":"<2-3 sentences>",
"thinking_steps":[{{"step":"<obs>","conclusion":"<meaning>"}}]}}"""
        try:
            resp_llm = _llm.chat.completions.create(
                model=os.getenv("ASI1_MODEL", "asi1-mini"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
            )
            raw = resp_llm.choices[0].message.content.replace("```json", "").replace("```", "").strip()
            data = json.loads(raw)
        except Exception as e:
            ctx.logger.error(f"Insights LLM failed: {e}")
            data = _mock_insights(summary, entertainer_id)

    for thought in data.get("thinking_steps", []):
        broadcast_thinking(thought["step"], thought.get("conclusion"), entertainer_id)

    round_tracker = ctx.storage.get("round_tracker") or {}
    current_round = round_tracker.get(entertainer_id, 1)
    round_tracker[entertainer_id] = current_round + 1
    ctx.storage.set("round_tracker", round_tracker)

    try:
        httpx.post(f"{BACKEND_URL}/analytics/insights", json={
            "entertainer_id": entertainer_id,
            "round_number": current_round,
            "best_venue_types": data["best_venue_types"],
            "avoid_segments": data["avoid_segments"],
            "best_pitch_angle": data["best_pitch_angle"],
            "optimal_price": data["optimal_price"],
            "insights_narrative": data["insights_narrative"],
        }, timeout=10)
    except Exception as e:
        ctx.logger.error(f"Failed to save insights: {e}")

    if os.getenv("SCAENA_AUTO_LOOP", "").lower() == "true":
        await ctx.send(AGENT1_ADDRESS, LearningInsights(
            entertainer_id=entertainer_id,
            best_venue_types=data["best_venue_types"],
            best_pitch_angle=data["best_pitch_angle"],
            accepted_rate=summary["accepted"] / max(summary["total_pitches"], 1),
            optimal_price=data["optimal_price"],
            avoid_segments=data["avoid_segments"],
            insights_narrative=data["insights_narrative"],
            round_number=current_round,
        ))
        await ctx.send(AGENT1_ADDRESS, TriggerResearch(entertainer_id=entertainer_id, round_number=current_round + 1))
        broadcast("complete", f"Round {current_round} insights sent to Agent 1. Loop closed.", entertainer_id)
    else:
        broadcast("complete", f"Round {current_round} insights ready for approval.", entertainer_id)
