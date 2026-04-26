from __future__ import annotations

import asyncio
import json
import os
import ssl
from dataclasses import dataclass
from typing import Any

try:
    import certifi

    _CERTIFI_CA = certifi.where()
    os.environ.setdefault("SSL_CERT_FILE", _CERTIFI_CA)
    os.environ.setdefault("REQUESTS_CA_BUNDLE", _CERTIFI_CA)
    _original_create_default_context = ssl.create_default_context

    def _create_certifi_context(*args, **kwargs):
        if "cafile" not in kwargs:
            kwargs["cafile"] = _CERTIFI_CA
        return _original_create_default_context(*args, **kwargs)

    ssl.create_default_context = _create_certifi_context
except Exception:
    pass

import httpx
from dotenv import load_dotenv
from uagents import Agent, Bureau, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)


load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")
NETWORK = os.getenv("AGENTVERSE_NETWORK", "testnet")
BUREAU_PORT = int(os.getenv("AGENTVERSE_BUREAU_PORT", "8110"))


def _ensure_event_loop():
    try:
        asyncio.get_event_loop_policy().get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())


@dataclass(frozen=True)
class BridgeSpec:
    role: str
    name: str
    seed_env: str
    address_env: str
    default_seed: str
    port: int
    description: str
    readme_path: str


BRIDGES = [
    BridgeSpec(
        role="agent1",
        name="scaena-market-research",
        seed_env="AGENT1_SEED",
        address_env="AGENT1_ADDRESS",
        default_seed="scaena-agentverse-market-research-bridge-la-hacks-2026",
        port=8101,
        description="Finds booking opportunities for artists using Scaena live market research.",
        readme_path="agentverse/README.agent1.md",
    ),
    BridgeSpec(
        role="agent2",
        name="scaena-outreach",
        seed_env="AGENT2_SEED",
        address_env="AGENT2_ADDRESS",
        default_seed="scaena-agentverse-outreach-bridge-la-hacks-2026",
        port=8102,
        description="Creates human booking pitches and summarizes active outreach conversations.",
        readme_path="agentverse/README.agent2.md",
    ),
    BridgeSpec(
        role="agent3",
        name="scaena-analytics",
        seed_env="AGENT3_SEED",
        address_env="AGENT3_ADDRESS",
        default_seed="scaena-agentverse-analytics-bridge-la-hacks-2026",
        port=8103,
        description="Reads Scaena Gmail and Outreach history to produce booking strategy insights.",
        readme_path="agentverse/README.agent3.md",
    ),
    BridgeSpec(
        role="agent4",
        name="scaena-pipeline",
        seed_env="AGENT4_SEED",
        address_env="AGENT4_ADDRESS",
        default_seed="scaena-agentverse-pipeline-bridge-la-hacks-2026",
        port=8104,
        description="Tracks secured deals, logistics, post-show status, and rebooking opportunities.",
        readme_path="agentverse/README.agent4.md",
    ),
]


async def _api(method: str, path: str, **kwargs) -> Any:
    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.request(method, f"{BACKEND_URL}{path}", **kwargs)
        response.raise_for_status()
        return response.json()


def _truncate(text: str | None, limit: int = 260) -> str:
    compact = " ".join(str(text or "").split())
    return compact if len(compact) <= limit else compact[: limit - 3].rstrip() + "..."


async def _active_entertainer() -> dict[str, Any] | None:
    entertainers = await _api("GET", "/entertainers/active")
    return entertainers[0] if entertainers else None


async def _agent1_response(user_text: str) -> str:
    ent = await _active_entertainer()
    if not ent:
        return "Scaena does not have an active artist profile yet. Open the app onboarding flow first."

    instruction = user_text.strip() or "Find high-fit booking opportunities."
    result = await _api("POST", "/outreach/research-refinement", json={
        "entertainer_id": ent["id"],
        "user_instruction": instruction,
    })
    venues = await _api("GET", f"/venues/{ent['id']}")
    top = sorted(venues, key=lambda item: item.get("fit_score") or 0, reverse=True)[:5]
    lines = [
        f"Agent 1 searched for opportunities for {ent.get('name', 'the artist')}.",
        f"Live discovery: {'yes' if result.get('live_discovery') else 'fallback/curated'}",
        "",
        "Top targets:",
    ]
    for idx, venue in enumerate(top, 1):
        score = venue.get("fit_score") or 0
        score = round(score * 100) if score <= 1 else round(score)
        lines.append(
            f"{idx}. {venue.get('name')} ({venue.get('venue_type') or 'venue'}, {score}% fit): "
            f"{_truncate(venue.get('why_fits'), 150)}"
        )
    return "\n".join(lines)


async def _agent2_response(user_text: str) -> str:
    ent = await _active_entertainer()
    if not ent:
        return "Scaena does not have an active artist profile yet."

    venues = await _api("GET", f"/venues/{ent['id']}")
    pitches = await _api("GET", f"/outreach/pitches/{ent['id']}")

    should_generate = any(word in user_text.lower() for word in ("generate", "draft", "pitch", "write"))
    if should_generate and venues:
        venue = sorted(venues, key=lambda item: item.get("fit_score") or 0, reverse=True)[0]
        draft = await _api("POST", "/outreach/pitch/generated", json={
            "entertainer_id": ent["id"],
            "venue_id": venue.get("id"),
            "venue_name": venue.get("name"),
            "venue_type": venue.get("venue_type"),
            "recipient_email": venue.get("contact_email"),
            "venue_contact_approach": venue.get("contact_approach"),
            "why_fits": venue.get("why_fits"),
            "source_url": venue.get("source_url"),
            "specific_examples": venue.get("specific_examples"),
            "proposed_rate": ent.get("current_rate"),
            "status": "draft",
        })
        return (
            f"Agent 2 generated a draft for {venue.get('name')} and saved it in Outreach.\n\n"
            f"Subject: {draft.get('pitch_subject')}\n\n"
            f"{_truncate(draft.get('pitch_body'), 900)}"
        )

    recent = sorted(pitches, key=lambda item: item.get("created_at") or "", reverse=True)[:5]
    if not recent:
        return "Agent 2 has no outreach drafts yet. Ask me to generate a pitch after Agent 1 finds venues."

    lines = [f"Agent 2 is tracking {len(pitches)} outreach item(s).", "", "Recent outreach:"]
    for pitch in recent:
        lines.append(
            f"- {pitch.get('venue_name')}: {pitch.get('status')} / {pitch.get('response_type') or 'no reply yet'}"
        )
    return "\n".join(lines)


async def _agent3_response(_: str) -> str:
    ent = await _active_entertainer()
    if not ent:
        return "Scaena does not have an active artist profile yet."

    ingest = await _api("POST", f"/analytics/auto-ingest/{ent['id']}")
    summary = await _api("GET", f"/analytics/summary/{ent['id']}")
    insights = await _api("GET", f"/analytics/insights/{ent['id']}")
    latest = insights[0] if insights else {}
    return (
        f"Agent 3 auto-ingested {ingest.get('message_count', 0)} chat message(s) "
        f"across {ingest.get('conversation_count', 0)} thread(s).\n\n"
        f"Response rate: {summary.get('response_rate', 0)}%\n"
        f"Booking rate: {summary.get('booking_rate', 0)}%\n"
        f"Best venue types: {_truncate(latest.get('best_venue_types') or 'still learning', 180)}\n"
        f"Strategy: {_truncate(latest.get('insights_narrative') or summary.get('top_insight') or 'Keep collecting replies.', 500)}"
    )


async def _agent4_response(_: str) -> str:
    active = await _api("GET", "/bookings/active")
    rebook = await _api("GET", "/bookings/completed-unrebooked")
    if not active and not rebook:
        return "Agent 4 has no secured deals yet. Once Agent 2 closes a booking, it will appear in Pipeline."

    lines = [
        f"Agent 4 is tracking {len(active)} active deal(s) and {len(rebook)} rebook-ready deal(s).",
        "",
        "Active pipeline:",
    ]
    for booking in active[:5]:
        checklist = booking.get("logistics_checklist") or {}
        done = sum(1 for value in checklist.values() if value)
        total = len(checklist)
        lines.append(
            f"- {booking.get('venue_name')}: {booking.get('conversation_stage')} "
            f"({done}/{total} logistics). Next: {_truncate(booking.get('next_action'), 140)}"
        )
    if rebook:
        lines.append("")
        lines.append("Ready for rebook:")
        for booking in rebook[:5]:
            lines.append(f"- {booking.get('venue_name')}: {_truncate(booking.get('post_show_notes') or booking.get('show_summary'), 140)}")
    return "\n".join(lines)


async def _dispatch(role: str, user_text: str) -> str:
    try:
        if role == "agent1":
            return await _agent1_response(user_text)
        if role == "agent2":
            return await _agent2_response(user_text)
        if role == "agent3":
            return await _agent3_response(user_text)
        if role == "agent4":
            return await _agent4_response(user_text)
        return "Unknown Scaena agent role."
    except httpx.ConnectError:
        return f"I could not reach Scaena at {BACKEND_URL}. Start the backend first, then retry this Agentverse chat."
    except httpx.HTTPStatusError as exc:
        return f"Scaena returned {exc.response.status_code}. Check the backend logs, then retry."
    except Exception as exc:
        return f"Agentverse bridge error: {type(exc).__name__}: {_truncate(str(exc), 240)}"


def _make_agent(spec: BridgeSpec) -> Agent:
    _ensure_event_loop()
    readme_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), spec.readme_path)
    agent = Agent(
        name=spec.name,
        seed=os.getenv(spec.seed_env, spec.default_seed),
        port=spec.port,
        mailbox=True,
        network=NETWORK,
        description=spec.description,
        readme_path=readme_path,
        publish_agent_details=True,
        store_message_history=True,
    )
    protocol = Protocol(spec=chat_protocol_spec)

    @protocol.on_message(ChatAcknowledgement)
    async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
        ctx.logger.debug("Agentverse chat acknowledgement from %s for %s", sender, msg.acknowledged_msg_id)

    @protocol.on_message(ChatMessage)
    async def handle_chat(ctx: Context, sender: str, msg: ChatMessage):
        await ctx.send(sender, ChatAcknowledgement(acknowledged_msg_id=msg.msg_id))
        user_text = msg.text().strip()
        ctx.logger.info("Agentverse chat from %s: %s", sender, _truncate(user_text, 120))
        response = await _dispatch(spec.role, user_text)
        await ctx.send(sender, ChatMessage(content=[TextContent(text=response)]))

    agent.include(protocol, publish_manifest=True)
    return agent


def _seed_status(spec: BridgeSpec, agent: Agent) -> str:
    expected_address = os.getenv(spec.address_env, "").strip()
    seed_is_default = os.getenv(spec.seed_env) is None
    if not expected_address:
        return "no expected address configured"
    if expected_address == agent.address:
        return "matches configured Agentverse address"

    seed_hint = "default seed" if seed_is_default else f"{spec.seed_env}"
    return (
        f"WARNING: {seed_hint} derives {agent.address}, but {spec.address_env} is "
        f"{expected_address}. This dashboard agent will not show active until "
        f"{spec.seed_env} is set to the matching seed phrase."
    )


def main():
    _ensure_event_loop()
    print("Starting Scaena Agentverse bridge agents")
    print(f"Backend: {BACKEND_URL}")
    print(f"Network: {NETWORK}")

    bureau = Bureau(port=BUREAU_PORT, network=NETWORK)
    for spec in BRIDGES:
        agent = _make_agent(spec)
        bureau.add(agent)
        print(f"{spec.role}: {spec.name} -> {agent.address} on port {spec.port}")
        print(f"  identity: {_seed_status(spec, agent)}")
    print("Open each inspector URL from the logs, connect via Mailbox, then use Chat with Agent in ASI:One.")
    bureau.run()


if __name__ == "__main__":
    main()
