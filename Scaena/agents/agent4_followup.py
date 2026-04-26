import os
import json
import httpx
from datetime import datetime
from agents.agent_runtime import Agent, Context
from agents.shared_models import FollowUpEngagement, BookingConversationUpdate, AGENT3_ADDRESS
from backend.services.pitch_generation import ensure_team_signoff, remove_long_dashes, team_name_for

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
_api_key = os.getenv("ASI1_API_KEY", "").strip()
_simulation_mode = not _api_key or _api_key in {"placeholder", "your_asi1_api_key_here"}

agent = Agent(
    name="scaena_pipeline_rebook",
    seed=os.getenv("AGENT4_SEED", "scaena_followup_seed"),
    port=8004,
)

try:
    from openai import OpenAI
    _llm = OpenAI(
        base_url=os.getenv("ASI1_BASE_URL", "https://api.asi1.ai/v1"),
        api_key=os.getenv("ASI1_API_KEY", "placeholder"),
    )
except Exception:
    _llm = None

_MOCK_FOLLOWUPS = {
    1: {
        "subject": "Quick follow-up for {name} performance inquiry",
        "body": "Hi,\n\nJust following up on our last note about {name} performing at {venue}.\n\nWe recently put together a performance reel. Happy to send it over if that helps with the decision.\n\nStill interested and flexible on dates.\n\nSincerely,\n{team}",
    },
    2: {
        "subject": "Re: {name} recent show highlights",
        "body": "Hi,\n\nWanted to check back in. Since our last message, {name} had a strong run of shows including a sold-out set last weekend, and audience response was excellent.\n\nWe would love to bring that energy to {venue}. Open to a trial booking if that works better.\n\nSincerely,\n{team}",
    },
    3: {
        "subject": "Final check-in for {name} availability",
        "body": "Hi,\n\nLast note. {name}'s availability for next month is filling up and we wanted to give {venue} first right of refusal before we commit elsewhere.\n\nNo pressure either way, but happy to hop on a quick call if helpful.\n\nSincerely,\n{team}",
    },
}

_MOCK_BOOKING_MSGS = {
    "secured": {
        "subject": "Confirmed logistics for {name} at {venue}",
        "body": "Hi,\n\nGreat news, excited to confirm the booking for {name}! A few quick logistics questions:\n\n• What time should he arrive for load-in/sound check?\n• Preferred payment method (Venmo, check, or invoice)?\n• Any specific set length or content guidelines?\n\nLooking forward to it!\n\nSincerely,\n{team}",
    },
    "logistics_pending": {
        "subject": "Logistics check for {name} at {venue}",
        "body": "Hi,\n\nWe are tightening up the show details for {name} at {venue}. Could you confirm load-in time, set length, payment method, and whether you need any promo assets from our side?\n\nSincerely,\n{team}",
    },
    "show_scheduled": {
        "subject": "Quick check-in before {venue}",
        "body": "Hi,\n\nJust checking in ahead of the show. Everything on our end is confirmed and {name} is looking forward to it.\n\nLet us know if anything has changed or if there is anything he should know before arriving.\n\nSincerely,\n{team}",
    },
    "post_show_followup": {
        "subject": "Thanks, {venue}! Great show",
        "body": "Hi,\n\nJust wanted to say thank you. Last night was a blast, and {name} had a great time with the crowd.\n\nWe would love to bring him back for another show whenever your schedule allows. Worth keeping him in mind for future bookings?\n\nSincerely,\n{team}",
    },
}

_STAGE_ALIASES = {
    "confirmed": "secured",
    "logistics": "logistics_pending",
    "pre_show": "show_scheduled",
    "post_show": "rebook_ready",
    "rebooking": "rebook_outreach_sent",
}


def broadcast(event_type: str, message: str, entertainer_id: str, **extra):
    try:
        httpx.post(f"{BACKEND_URL}/agent-events/broadcast", json={
            "agent_id": "agent4", "event_type": event_type,
            "message": message, "entertainer_id": entertainer_id, **extra
        }, timeout=5)
    except Exception:
        pass


def _normalize_message(message: dict, name: str) -> dict:
    return {
        **message,
        "subject": remove_long_dashes(message.get("subject")),
        "body": ensure_team_signoff(remove_long_dashes(message.get("body")), name),
    }


def _format_template(template: dict, name: str, venue: str) -> dict:
    return {
        "subject": template["subject"].format(name=name, venue=venue, team=team_name_for(name)),
        "body": template["body"].format(name=name, venue=venue, team=team_name_for(name)),
    }


def _get_entertainer_name(entertainer_id: str) -> str:
    try:
        resp = httpx.get(f"{BACKEND_URL}/entertainers/{entertainer_id}", timeout=5)
        return resp.json().get("name", "the artist")
    except Exception:
        return "the artist"


def _get_entertainer_type(entertainer_id: str) -> str:
    try:
        resp = httpx.get(f"{BACKEND_URL}/entertainers/{entertainer_id}", timeout=5)
        return resp.json().get("type", "performer")
    except Exception:
        return "performer"


@agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info(f"Agent 4 (Follow-Up & Post-Booking) started: {agent.address}")


@agent.on_interval(period=259200)
async def run_all_tasks(ctx: Context):
    ctx.logger.info("Agent 4: Running follow-up and post-booking checks...")

    # Follow-ups
    try:
        resp = httpx.get(f"{BACKEND_URL}/outreach/pending-followup", timeout=10)
        for pitch in resp.json():
            await handle_followup(ctx, pitch)
    except Exception as e:
        ctx.logger.error(f"Follow-up check failed: {e}")

    # Post-booking
    try:
        resp = httpx.get(f"{BACKEND_URL}/bookings/active", timeout=10)
        for booking in resp.json():
            await handle_booking_conversation(ctx, booking)
    except Exception as e:
        ctx.logger.error(f"Post-booking check failed: {e}")

    # Rebooking
    try:
        resp = httpx.get(f"{BACKEND_URL}/bookings/completed-unrebooked", timeout=10)
        for booking in resp.json():
            await handle_rebooking(ctx, booking)
    except Exception as e:
        ctx.logger.error(f"Rebooking check failed: {e}")

    await check_seasonal_reengagement(ctx)


async def handle_followup(ctx: Context, pitch: dict):
    pitch_id = pitch["pitch_id"]
    followup_number = pitch.get("followup_count", 0) + 1
    eid = pitch["entertainer_id"]
    venue = pitch["venue_name"]

    if followup_number > 3:
        try:
            httpx.patch(f"{BACKEND_URL}/outreach/pitch/{pitch_id}", json={"status": "closed_no_response"}, timeout=5)
        except Exception:
            pass
        broadcast("followup_closed", f"Closed {venue} after 3 unanswered follow-ups.", eid, target=venue)
        return

    name = _get_entertainer_name(eid)

    if _simulation_mode:
        template = _MOCK_FOLLOWUPS[followup_number]
        followup = _format_template(template, name, venue)
    else:
        instructions = {
            1: "Follow-up #1. Brief, offer to send a performance reel. Under 70 words.",
            2: "Follow-up #2. Add social proof, recent show success. Under 70 words.",
            3: "Follow-up #3, final. Gentle urgency. Under 60 words.",
        }
        prompt = f"Generate follow-up #{followup_number} for {pitch['entertainer_type']} pitching {venue}.\nArtist: {name}\nWrite from {team_name_for(name)}'s perspective using we/our team, not from the artist personally.\nSign off exactly with: Sincerely, then {team_name_for(name)} on the next line.\nOriginal subject: {pitch['pitch_subject']}\n{instructions[followup_number]}\nDo not use em dashes or en dashes.\nReturn ONLY JSON: {{\"subject\":\"...\",\"body\":\"...\"}}"
        try:
            resp_llm = _llm.chat.completions.create(
                model=os.getenv("ASI1_MODEL", "asi1-mini"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
            )
            raw = resp_llm.choices[0].message.content.replace("```json", "").replace("```", "").strip()
            followup = json.loads(raw)
        except Exception as e:
            ctx.logger.error(f"Follow-up gen failed: {e}")
            template = _MOCK_FOLLOWUPS[followup_number]
            followup = _format_template(template, name, venue)

    followup = _normalize_message(followup, name)

    try:
        httpx.post(f"{BACKEND_URL}/outreach/followup", json={
            "pitch_id": pitch_id,
            "entertainer_id": eid,
            "followup_number": followup_number,
            "subject": followup["subject"],
            "body": followup["body"],
            "status": "draft",
        }, timeout=10)
        broadcast("followup_ready", f"Follow-up #{followup_number} ready for {venue}", eid, target=venue, followup_number=followup_number)
    except Exception as e:
        ctx.logger.error(f"Failed to save follow-up: {e}")
        return

    await ctx.send(AGENT3_ADDRESS, FollowUpEngagement(
        entertainer_id=eid,
        venue_id=pitch_id,
        followup_number=followup_number,
        response_received=False,
        response_type=None,
        timestamp=str(datetime.utcnow()),
    ))


async def handle_booking_conversation(ctx: Context, booking: dict):
    stage = _STAGE_ALIASES.get(booking.get("conversation_stage", "secured"), booking.get("conversation_stage", "secured"))
    eid = booking["entertainer_id"]
    target_id = booking["target_id"]
    booking_id = booking["id"]
    venue = booking["venue_name"]

    if stage not in _MOCK_BOOKING_MSGS:
        return

    broadcast("working", f"Drafting {stage} message for {venue}...", eid, target_id=target_id, stage=stage)
    name = _get_entertainer_name(eid)

    if _simulation_mode:
        template = _MOCK_BOOKING_MSGS[stage]
        message = _format_template(template, name, venue)
    else:
        stage_prompts = {
            "secured": f"Confirm logistics with {venue}: arrival, sound check, payment. 100 words max.",
            "logistics_pending": f"Ask {venue} to confirm remaining logistics: load-in, set length, payment, promo assets. 90 words max.",
            "show_scheduled": f"Check in 2 days before show at {venue}. 60 words max.",
            "post_show_followup": f"Post-show thank you to {venue}, hint at rebooking. 80 words max.",
        }
        prompt = f"{stage_prompts[stage]}\nPerformer: {name}\nWrite from {team_name_for(name)}'s perspective using we/our team, not from the artist personally.\nSign off exactly with: Sincerely, then {team_name_for(name)} on the next line.\nDo not use em dashes or en dashes.\nReturn ONLY JSON: {{\"subject\":\"...\",\"body\":\"...\"}}"
        try:
            resp_llm = _llm.chat.completions.create(
                model=os.getenv("ASI1_MODEL", "asi1-mini"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
            )
            raw = resp_llm.choices[0].message.content.replace("```json", "").replace("```", "").strip()
            message = json.loads(raw)
        except Exception as e:
            ctx.logger.error(f"Booking msg gen failed: {e}")
            template = _MOCK_BOOKING_MSGS.get(stage, _MOCK_BOOKING_MSGS["secured"])
            message = _format_template(template, name, venue)

    message = _normalize_message(message, name)

    try:
        httpx.post(f"{BACKEND_URL}/bookings/conversation-message", json={
            "booking_id": booking_id,
            "entertainer_id": eid,
            "target_id": target_id,
            "stage": stage,
            "subject": message["subject"],
            "body": message["body"],
            "status": "draft",
        }, timeout=10)
        broadcast("booking_message_ready", f"{stage.replace('_', ' ').title()} message ready for {venue}", eid, target_id=target_id, stage=stage)
    except Exception as e:
        ctx.logger.error(f"Failed to save booking message: {e}")
        return

    await ctx.send(AGENT3_ADDRESS, BookingConversationUpdate(
        entertainer_id=eid,
        target_id=target_id,
        booking_id=booking_id,
        message_sent=message["body"],
        response_received=None,
        conversation_stage=stage,
        timestamp=str(datetime.utcnow()),
    ))


async def handle_rebooking(ctx: Context, booking: dict):
    eid = booking["entertainer_id"]
    venue = booking["venue_name"]
    target_id = booking["target_id"]
    booking_id = booking["id"]

    broadcast("working", f"Sending {venue} to Agent 2 for rebook outreach...", eid, target_id=target_id)

    try:
        resp = httpx.post(f"{BACKEND_URL}/outreach/pitch/rebook", json={
            "entertainer_id": eid,
            "booking_id": booking_id,
            "status": "draft",
        }, timeout=10)
        resp.raise_for_status()
        payload = resp.json()
        pitch_id = payload.get("pitch_id", "")
        pitch_body = payload.get("pitch_body", "Rebook draft created in Outreach.")
        broadcast("rebook_ready", f"Rebooking draft sent to Outreach for {venue}", eid, target_id=target_id, pitch_id=pitch_id)
    except Exception as e:
        ctx.logger.error(f"Failed to save rebooking: {e}")
        return

    await ctx.send(AGENT3_ADDRESS, BookingConversationUpdate(
        entertainer_id=eid,
        target_id=target_id,
        booking_id=booking_id,
        message_sent=pitch_body,
        response_received=None,
        conversation_stage="rebooking",
        timestamp=str(datetime.utcnow()),
    ))


async def check_seasonal_reengagement(ctx: Context):
    month = datetime.now().month
    seasons = {
        3: "Spring festival season - venues booking outdoor events",
        6: "Summer festival peak - outdoor venues and music festivals actively booking",
        8: "Back-to-campus season - student boards and bars booking fall shows",
        10: "Fall concert season - campuses, bars, and music venues booking hip-hop shows",
        1: "New Year bookings - venues setting Q1 lineups",
    }
    note = seasons.get(month)
    if not note:
        return

    try:
        resp = httpx.get(f"{BACKEND_URL}/outreach/rejected-or-later", timeout=10)
        stale = resp.json()
    except Exception as e:
        ctx.logger.error(f"Stale pitches fetch failed: {e}")
        return

    for pitch in stale[:5]:
        eid = pitch["entertainer_id"]
        name = _get_entertainer_name(eid)
        venue = pitch["venue_name"]

        if _simulation_mode:
            reengage = {
                "subject": f"{note.split(' - ')[0].strip()} - {name} available",
                "body": f"Hi,\n\n{note}. We wanted to check back in because {name} would be a strong fit for {venue}'s upcoming programming.\n\nWould you be open to connecting?\n\nSincerely,\n{team_name_for(name)}",
            }
        else:
            prompt = f"Seasonal re-engagement to {venue}. Context: {note}. Performer: {name} ({pitch['entertainer_type']}). Write from {team_name_for(name)}'s perspective using we/our team, not from the artist personally. Sign off exactly with: Sincerely, then {team_name_for(name)} on the next line. 50 words max. Do not use em dashes or en dashes. Return ONLY JSON: {{\"subject\":\"...\",\"body\":\"...\"}}"
            try:
                resp_llm = _llm.chat.completions.create(
                    model=os.getenv("ASI1_MODEL", "asi1-mini"),
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=200,
                )
                raw = resp_llm.choices[0].message.content.replace("```json", "").replace("```", "").strip()
                reengage = json.loads(raw)
            except Exception as e:
                ctx.logger.error(f"Re-engagement gen failed: {e}")
                continue

        reengage = _normalize_message(reengage, name)

        try:
            httpx.post(f"{BACKEND_URL}/outreach/reengagement", json={
                "pitch_id": pitch.get("pitch_id"),
                "entertainer_id": eid,
                "subject": reengage["subject"],
                "body": reengage["body"],
                "reason": note,
                "status": "draft",
            }, timeout=10)
            broadcast("reengagement_ready", f"Seasonal re-engagement ready for {venue}", eid, target=venue)
        except Exception as e:
            ctx.logger.error(f"Re-engagement save failed: {e}")
