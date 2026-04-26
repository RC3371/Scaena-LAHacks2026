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
from backend.services.pitch_generation import generate_pitch_for_venue

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
_api_key = os.getenv("ASI1_API_KEY", "").strip()
_simulation_mode = not _api_key or _api_key in {"placeholder", "your_asi1_api_key_here"}

agent = Agent(
    name="scaena_outreach_pitching",
    seed=os.getenv("AGENT2_SEED", "scaena_pitching_seed"),
    port=8002,
    address=os.getenv("AGENT2_ADDRESS"),
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


def _auto_send_pitch(pitch_id: str, venue_name: str, entertainer_id: str, ctx: Context) -> bool:
    try:
        send_resp = httpx.post(f"{BACKEND_URL}/gmail/send-pitch/{pitch_id}", timeout=20)
        send_resp.raise_for_status()
        send_result = send_resp.json()
        event_type = "gmail_dry_run" if send_result.get("dry_run") else "gmail_auto_sent"
        message = (
            f"Auto-send dry run complete for {venue_name}."
            if send_result.get("dry_run")
            else f"Auto-sent Gmail pitch to {venue_name}."
        )
        broadcast(
            event_type,
            message,
            entertainer_id,
            target=venue_name,
            pitch_id=pitch_id,
            recipient=send_result.get("recipient"),
            message_id=send_result.get("message_id"),
            thread_id=send_result.get("thread_id"),
        )
        return True
    except Exception as e:
        ctx.logger.error(f"Gmail auto-send failed for {venue_name}: {e}")
        broadcast(
            "error",
            f"Gmail auto-send failed for {venue_name}. Draft stayed in Outreach.",
            entertainer_id,
            target=venue_name,
            pitch_id=pitch_id,
        )
        return False


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

        pitch = generate_pitch_for_venue(entertainer, venue, msg.recommended_rate)
        if pitch.get("generation_source") == "fallback" and pitch.get("generation_error"):
            ctx.logger.error(f"Pitch gen fell back for {venue['name']}: {pitch['generation_error']}")

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
                "status": "draft",
            }, timeout=10)
            resp.raise_for_status()
            pitch_id = resp.json().get("pitch_id", "")
            pitch_ids.append(pitch_id)
            auto_sent = False
            if outreach_mode == "auto_pitch" and pitch_id:
                auto_sent = _auto_send_pitch(pitch_id, venue["name"], msg.entertainer_id, ctx)
            status = "sent" if auto_sent else "draft"
            broadcast("pitch_ready", f"Pitch ready for {venue['name']} - {status}", msg.entertainer_id, target=venue["name"], pitch_id=pitch_id, status=status)
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
