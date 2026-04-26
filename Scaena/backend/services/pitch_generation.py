from __future__ import annotations

import hashlib
import json
import math
import os
import re
from typing import Any

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - dependency is optional in dev shells
    OpenAI = None


def generate_pitch_for_venue(
    entertainer: dict[str, Any],
    venue: dict[str, Any],
    rate: float | None = None,
    strategy_instruction: str | None = None,
) -> dict[str, str]:
    """Generate a venue-specific booking pitch.

    Uses ASI-1 when configured. Falls back to deterministic human-tone templates so the
    app never returns the old generic "I came across..." draft.
    """
    recommended_rate = float(rate or entertainer.get("current_rate") or 350)
    greeting = greeting_for(venue)

    if _asi1_ready():
        try:
            pitch = {
                **_generate_with_asi1(entertainer, venue, recommended_rate, strategy_instruction),
                "generation_source": "asi1",
            }
            return _normalize_pitch(pitch, entertainer, greeting)
        except Exception as exc:
            fallback = _fallback_pitch(entertainer, venue, recommended_rate)
            fallback["generation_source"] = "fallback"
            fallback["generation_error"] = _safe_error(exc)
            return _normalize_pitch(fallback, entertainer, greeting)

    fallback = _fallback_pitch(entertainer, venue, recommended_rate)
    fallback["generation_source"] = "fallback"
    return _normalize_pitch(fallback, entertainer, greeting)


def generate_reply_draft(
    entertainer: dict[str, Any],
    venue: dict[str, Any],
    pitch: dict[str, Any],
    latest_reply: str,
    analysis: dict[str, Any] | None = None,
    conversation_messages: list[dict[str, Any]] | None = None,
    prior_context: str | None = None,
) -> dict[str, str]:
    """Generate the next email in an existing venue conversation."""
    greeting = greeting_for(venue, pitch)
    memory = build_conversation_memory(conversation_messages or [], latest_reply, pitch, entertainer)
    if _asi1_ready():
        try:
            generated = {
                **_generate_reply_with_asi1(entertainer, venue, pitch, latest_reply, analysis or {}, memory, prior_context),
                "generation_source": "asi1",
            }
            return _normalize_pitch(generated, entertainer, greeting)
        except Exception as exc:
            fallback = _fallback_reply_draft(entertainer, venue, pitch, latest_reply, analysis or {}, memory, prior_context)
            fallback["generation_source"] = "fallback"
            fallback["generation_error"] = _safe_error(exc)
            return _normalize_pitch(fallback, entertainer, greeting)

    fallback = _fallback_reply_draft(entertainer, venue, pitch, latest_reply, analysis or {}, memory, prior_context)
    fallback["generation_source"] = "fallback"
    return _normalize_pitch(fallback, entertainer, greeting)


def generate_rebook_pitch(
    entertainer: dict[str, Any],
    booking: dict[str, Any],
    rate: float | None = None,
    prior_context: str | None = None,
) -> dict[str, str]:
    """Generate a rebooking email after a successful previous show."""
    recommended_rate = float(rate or booking.get("agreed_rate") or entertainer.get("current_rate") or 350)
    greeting = greeting_for(booking)

    if _asi1_ready():
        try:
            generated = {
                **_generate_rebook_with_asi1(entertainer, booking, recommended_rate, prior_context),
                "generation_source": "asi1",
            }
            return _normalize_pitch(generated, entertainer, greeting)
        except Exception as exc:
            fallback = _fallback_rebook_pitch(entertainer, booking, recommended_rate, prior_context)
            fallback["generation_source"] = "fallback"
            fallback["generation_error"] = _safe_error(exc)
            return _normalize_pitch(fallback, entertainer, greeting)

    fallback = _fallback_rebook_pitch(entertainer, booking, recommended_rate, prior_context)
    fallback["generation_source"] = "fallback"
    return _normalize_pitch(fallback, entertainer, greeting)


def _asi1_ready() -> bool:
    key = os.getenv("ASI1_API_KEY", "").strip()
    return bool(OpenAI and key and key not in {"placeholder", "your_asi1_api_key_here"})


def _generate_with_asi1(
    entertainer: dict[str, Any],
    venue: dict[str, Any],
    rate: float,
    strategy_instruction: str | None,
) -> dict[str, str]:
    client = OpenAI(
        base_url=os.getenv("ASI1_BASE_URL", "https://api.asi1.ai/v1"),
        api_key=os.getenv("ASI1_API_KEY", "placeholder"),
    )
    prompt = _build_prompt(entertainer, venue, rate, strategy_instruction)
    response = client.chat.completions.create(
        model=os.getenv("ASI1_MODEL", "asi1-mini"),
        messages=[
            {
                "role": "system",
                "content": (
                    "You write concise, specific booking outreach emails for performing artists. "
                    "Sound like a real person, not a sales automation tool."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.75,
        max_tokens=650,
    )
    raw = response.choices[0].message.content or ""
    pitch = _parse_pitch_json(raw)
    subject = str(pitch.get("subject", "")).strip()
    body = str(pitch.get("body", "")).strip()
    if not subject or not body:
        raise ValueError("ASI-1 returned an incomplete pitch")
    return {"subject": subject, "body": body}


def _generate_reply_with_asi1(
    entertainer: dict[str, Any],
    venue: dict[str, Any],
    pitch: dict[str, Any],
    latest_reply: str,
    analysis: dict[str, Any],
    memory: dict[str, Any],
    prior_context: str | None,
) -> dict[str, str]:
    client = OpenAI(
        base_url=os.getenv("ASI1_BASE_URL", "https://api.asi1.ai/v1"),
        api_key=os.getenv("ASI1_API_KEY", "placeholder"),
    )
    artist_name = entertainer.get("name", "The Artist")
    recipient_name = recipient_name_for(venue, pitch)
    greeting = greeting_for(venue, pitch)
    date_guidance = (
        "- The latest reply includes a specific date or time. Do not ask for dates again and do not ask them to confirm the same date. Acknowledge it, state whether we can work with it, and move to missing logistics only.\n"
        if reply_has_specific_date(latest_reply)
        else ""
    )
    prompt = f"""Write the next email reply in this booking conversation.

Artist:
- Name: {artist_name}
- Type: {entertainer.get("type", "performer")}
- Genre/style: {entertainer.get("genre", "")}
- Location: {entertainer.get("location", "")}
- Rate: ${float(pitch.get("proposed_rate") or entertainer.get("current_rate") or 350):.0f}/show
- Highlights/goals: {entertainer.get("highlights", "")}

Venue/thread:
- Venue: {venue.get("name") or pitch.get("venue_name", "")}
- Venue type: {venue.get("venue_type", "")}
- Recipient/contact: {recipient_name or "unknown"}
- Contact email: {venue.get("contact_email") or pitch.get("recipient_email", "")}
- Original subject: {pitch.get("pitch_subject", "")}
- Last venue reply:
{latest_reply}

Conversation memory:
{memory_as_prompt(memory)}

Prior same venue/company context:
{prior_context.strip() if prior_context and prior_context.strip() else "No prior same-venue history found."}

Agent 3 read:
- Interest level: {analysis.get("interest_level", "")}
- Response type: {analysis.get("response_type", "")}
- Next action: {analysis.get("what_to_do_next", "")}

Requirements:
- Under 130 words.
- Start the email exactly with: {greeting}
- Write from {team_name_for(artist_name)}'s perspective using "we" and "our team".
- Do not write as the artist personally.
- Respond directly to the latest reply.
- Keep the greeting consistent with the recipient/contact above. Keep the signoff consistent with the sender/team below.
- Do not ask for information the recipient already gave in the latest reply.
- Honor every agreement in conversation memory, especially agreed date, agreed rate, EPK/materials already sent, and any concessions already made.
- Use prior same-venue context to remember the relationship and avoid repeating old questions, but do not treat old dates/rates as current unless the latest thread confirms them.
- Follow the price policy in conversation memory. Accept venue counters inside the flexible acceptance range. If a counter is below that range, politely counter at the floor instead of accepting it.
- Ask at most one concise question. Ask two only if both are true blockers.
- Do not ask for dates, rate, EPK, or confirmation if conversation memory already contains them.
- If logistics are missing, ask for only the next 1-2 most important logistics items, usually set time and load-in.
- Never invent links, EPK URLs, venue capacities, audience counts, or placeholders.
{date_guidance}- If they ask about price, answer clearly with the rate and one flexible option.
- If they are interested but have not suggested a date, move toward dates, reel/EPK, or a quick call.
- If they reject, be gracious and leave the door open.
- Avoid closed-door wording about ending the thread or waiting for a better season. Prefer simple open language like "Let us know if you are interested in a future date."
- Sign off exactly with:
  Sincerely,
  {team_name_for(artist_name)}
- Do not use em dashes or en dashes.
- Return ONLY valid JSON in this shape: {{"subject":"...","body":"..."}}"""
    response = client.chat.completions.create(
        model=os.getenv("ASI1_MODEL", "asi1-mini"),
        messages=[
            {
                "role": "system",
                "content": "You write concise booking conversation replies for an artist's agency/team.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=550,
    )
    raw = response.choices[0].message.content or ""
    parsed = _parse_pitch_json(raw)
    subject = str(parsed.get("subject", "")).strip()
    body = str(parsed.get("body", "")).strip()
    if not subject or not body:
        raise ValueError("ASI-1 returned an incomplete reply draft")
    return {"subject": subject, "body": body}


def _generate_rebook_with_asi1(
    entertainer: dict[str, Any],
    booking: dict[str, Any],
    rate: float,
    prior_context: str | None,
) -> dict[str, str]:
    client = OpenAI(
        base_url=os.getenv("ASI1_BASE_URL", "https://api.asi1.ai/v1"),
        api_key=os.getenv("ASI1_API_KEY", "placeholder"),
    )
    artist_name = entertainer.get("name", "The Artist")
    venue_name = booking.get("venue_name", "the venue")
    prompt = f"""Write a rebooking outreach email after a previous successful show.

Artist:
- Name: {artist_name}
- Type: {entertainer.get("type", "performer")}
- Genre/style: {entertainer.get("genre", "")}
- Location: {entertainer.get("location", "")}
- Highlights/goals: {entertainer.get("highlights", "")}

Previous booking:
- Venue: {venue_name}
- Previous agreed rate: ${rate:.0f}/show
- Show summary: {booking.get("show_summary", "")}
- Current booking stage: {booking.get("conversation_stage", "")}

Prior same venue/company context:
{prior_context.strip() if prior_context and prior_context.strip() else "No prior same-venue history found."}

Directive:
- This is not an initial booking pitch.
- Ask whether {venue_name} would like to bring {artist_name} back for another show.
- Reference that they have already worked together.
- Use the prior context to stay consistent with earlier names, rates, dates, and logistics, but do not invent new commitments.
- Keep the tone human, warm, and specific.
- Under 120 words.
- Write from {team_name_for(artist_name)}'s perspective using "we" and "our team".
- Do not write as the artist personally.
- Sign off exactly with:
  Sincerely,
  {team_name_for(artist_name)}
- Do not use em dashes or en dashes.
- Avoid closed-door wording about ending the thread or waiting for a better season.
- Return ONLY valid JSON in this shape: {{"subject":"...","body":"..."}}"""
    response = client.chat.completions.create(
        model=os.getenv("ASI1_MODEL", "asi1-mini"),
        messages=[
            {
                "role": "system",
                "content": "You write concise rebooking emails for an artist's agency/team.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=500,
    )
    raw = response.choices[0].message.content or ""
    parsed = _parse_pitch_json(raw)
    subject = str(parsed.get("subject", "")).strip()
    body = str(parsed.get("body", "")).strip()
    if not subject or not body:
        raise ValueError("ASI-1 returned an incomplete rebook pitch")
    return {"subject": subject, "body": body}


def _build_prompt(
    entertainer: dict[str, Any],
    venue: dict[str, Any],
    rate: float,
    strategy_instruction: str | None,
) -> str:
    examples = _examples_as_text(venue.get("specific_examples"))
    revision = f"\nUser revision instruction: {strategy_instruction.strip()}\n" if strategy_instruction and strategy_instruction.strip() else ""
    recipient_name = recipient_name_for(venue)
    greeting = greeting_for(venue)
    return f"""Write a personalized booking pitch email.

Artist profile:
- Name: {entertainer.get("name", "The Artist")}
- Type: {entertainer.get("type", "performer")}
- Genre/style: {entertainer.get("genre", "")}
- Location: {entertainer.get("location", "")}
- Experience: {entertainer.get("experience_years", 0)} years
- Social following: {entertainer.get("social_followers", 0)}
- Highlights/goals: {entertainer.get("highlights", "")}
- Rate: ${rate:.0f}/show

Target venue/organization:
- Name: {venue.get("name", "")}
- Type: {venue.get("venue_type", "")}
- Recipient/contact: {recipient_name or "unknown"}
- Contact email: {venue.get("contact_email", "")}
- Contact approach: {venue.get("contact_approach", "")}
- Why it fits: {venue.get("why_fits", "")}
- Examples/signals: {examples}
- Source URL: {venue.get("source_url", "")}
{revision}

Requirements:
- Under 150 words.
- Start the email exactly with: {greeting}
- Be specific to the venue type and audience.
- Mention the rate naturally, not aggressively.
- Write from the user's agency/team perspective in first person plural.
- Use "we", "our team", or "we represent {entertainer.get("name", "The Artist")}". Do not write as if you are the artist personally.
- Keep the greeting consistent with the recipient/contact above. Keep the signoff consistent with the sender/team below.
- Sign off exactly with:
  Sincerely,
  {team_name_for(entertainer.get("name", "The Artist"))}
- Never include placeholders like "[Your Name]", "[Artist Name]", or bracketed fields.
- Do not use em dashes or en dashes. Use commas, periods, parentheses, or simple hyphens instead.
- Do not include audience counts, venue capacities, dates, awards, or hard metrics unless they appear in the artist profile or target venue notes above.
- Do not use generic lines like "I came across your venue" or "my act would be a great fit".
- Avoid closed-door wording about ending the thread or waiting for a better season.
- Do not invent hard claims, dates, or numbers that are not in the profile.
- Return ONLY valid JSON in this shape: {{"subject":"...","body":"..."}}"""


def _parse_pitch_json(raw: str) -> dict[str, Any]:
    cleaned = raw.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.S)
        if not match:
            raise
        return json.loads(match.group(0))


def _examples_as_text(value: Any) -> str:
    if not value:
        return ""
    if isinstance(value, list):
        return "; ".join(str(item) for item in value if item)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return "; ".join(str(item) for item in parsed if item)
        except json.JSONDecodeError:
            pass
        return value
    return str(value)


def _safe_error(exc: Exception) -> str:
    message = str(exc)
    message = re.sub(r"sk_[A-Za-z0-9]+", "[redacted]", message)
    return message[:240]


def build_conversation_memory(
    messages: list[dict[str, Any]],
    latest_reply: str,
    pitch: dict[str, Any] | None = None,
    entertainer: dict[str, Any] | None = None,
) -> dict[str, Any]:
    pitch = pitch or {}
    entertainer = entertainer or {}
    all_messages = [
        {
            "direction": str(msg.get("direction") or ""),
            "body": str(msg.get("body") or ""),
            "created_at": str(msg.get("created_at") or ""),
        }
        for msg in messages
        if str(msg.get("body") or "").strip()
    ]
    if latest_reply and not any(str(msg.get("body") or "").strip() == latest_reply.strip() for msg in all_messages):
        all_messages.append({"direction": "inbound", "body": latest_reply, "created_at": ""})

    inbound_text = "\n".join(msg["body"] for msg in all_messages if msg["direction"] == "inbound")
    outbound_text = "\n".join(msg["body"] for msg in all_messages if msg["direction"] == "outbound")
    all_text = "\n".join(msg["body"] for msg in all_messages)

    price_policy = price_policy_for(entertainer, pitch)
    date_mentions = _unique_preserve_order(_extract_date_mentions(all_text))
    latest_dates = _extract_date_mentions(latest_reply)
    inbound_rates = _extract_money_mentions(inbound_text)
    outbound_rates = _extract_money_mentions(outbound_text)
    all_rates = _extract_money_mentions(all_text)
    latest_rate_amounts = _extract_money_values(latest_reply)
    all_rate_amounts = _extract_money_values(all_text)
    thread_rate_amount = _latest(all_rate_amounts)
    latest_rate_amount = _latest(latest_rate_amounts)
    rate_to_evaluate = latest_rate_amount or thread_rate_amount or pitch.get("proposed_rate") or entertainer.get("current_rate")
    thread_rate = _format_rate(thread_rate_amount) if thread_rate_amount is not None else _latest(all_rates)
    agreed_rate = thread_rate or _format_rate(pitch.get("proposed_rate") or entertainer.get("current_rate"))
    rate_status = _rate_status(rate_to_evaluate, price_policy)
    requested_epk = bool(re.search(r"\b(epk|press kit|media kit|reel|deck)\b", inbound_text, flags=re.I))
    sent_epk = bool(re.search(r"\b(epk|press kit|media kit|reel)\b", outbound_text, flags=re.I))

    logistics_known = {
        "set_time": bool(re.search(r"\b(set time|start time|doors|show time|performance time|time is|at \d{1,2}(:\d{2})?\s*(am|pm))\b", all_text, flags=re.I)),
        "load_in": bool(re.search(r"\b(load[- ]?in|soundcheck|sound check|arrival)\b", all_text, flags=re.I)),
        "set_length": bool(re.search(r"\b(set length|\d{2}\s*(minute|min)|hour set|runtime)\b", all_text, flags=re.I)),
        "payment": bool(re.search(r"\b(payment|invoice|deposit|venmo|check|ach|paypal|paid)\b", all_text, flags=re.I)),
    }
    asked_logistics = bool(re.search(r"\b(set time|load[- ]?in|soundcheck|sound check|payment|invoice|set length)\b", outbound_text, flags=re.I))

    agreements: list[str] = []
    if date_mentions:
        agreements.append(f"Date/time mentioned: {', '.join(date_mentions[-2:])}")
    if thread_rate:
        agreements.append(f"Rate discussed/agreed: {agreed_rate}")
    elif agreed_rate:
        agreements.append(f"Current proposed rate: {agreed_rate}")
    if requested_epk:
        agreements.append("Recipient asked for EPK/reel/materials")
    if sent_epk:
        agreements.append("Sender already addressed EPK/reel/materials")
    if asked_logistics:
        agreements.append("Sender already asked for logistics details")

    recent_history = [
        f"{'Recipient' if msg['direction'] == 'inbound' else 'Sender'}: {_compact_text(msg['body'], 220)}"
        for msg in all_messages[-6:]
    ]
    missing_logistics = [label for label, known in [
        ("set time", logistics_known["set_time"]),
        ("load-in", logistics_known["load_in"]),
        ("set length", logistics_known["set_length"]),
        ("payment/invoice", logistics_known["payment"]),
    ] if not known]

    return {
        "agreements": agreements,
        "date_mentions": date_mentions,
        "latest_reply_dates": latest_dates,
        "rates": all_rates,
        "agreed_rate": agreed_rate,
        "rate_from_thread": bool(thread_rate),
        "latest_rate_amount": latest_rate_amount,
        "thread_rate_amount": thread_rate_amount,
        "price_policy": price_policy,
        "rate_is_acceptable": rate_status["acceptable"],
        "rate_is_within_flexible_range": rate_status["within_range"],
        "rate_is_below_flexible_range": rate_status["below_range"],
        "rate_is_above_flexible_range": rate_status["above_range"],
        "price_guidance": rate_status["guidance"],
        "requested_epk": requested_epk,
        "sent_epk": sent_epk,
        "asked_logistics": asked_logistics,
        "logistics_known": logistics_known,
        "missing_logistics": missing_logistics,
        "recent_history": recent_history,
    }


def memory_as_prompt(memory: dict[str, Any]) -> str:
    lines: list[str] = []
    agreements = memory.get("agreements") or []
    if agreements:
        lines.append("Known agreements and facts:")
        lines.extend(f"- {item}" for item in agreements)
    else:
        lines.append("Known agreements and facts: none yet")

    missing = memory.get("missing_logistics") or []
    if missing:
        lines.append(f"Missing logistics, ask sparingly: {', '.join(missing[:3])}")
    else:
        lines.append("Missing logistics: none obvious")

    policy = memory.get("price_policy") or {}
    if policy:
        lines.append(
            "Price policy: "
            f"target {policy.get('target_range_display')}, "
            f"flexible acceptance range {policy.get('flex_range_display')}. "
            f"{memory.get('price_guidance', '')}"
        )

    history = memory.get("recent_history") or []
    if history:
        lines.append("Recent thread:")
        lines.extend(f"- {item}" for item in history)
    return "\n".join(lines)


def price_policy_for(
    entertainer: dict[str, Any] | None = None,
    pitch: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compute the booking price window with a 10% margin rounded to $50."""
    entertainer = entertainer or {}
    pitch = pitch or {}
    profile_range = _extract_rate_range(
        str(entertainer.get("highlights") or ""),
        str(entertainer.get("links") or ""),
        str(pitch.get("strategy_note") or ""),
    )
    fallback_rate = _as_float(pitch.get("proposed_rate")) or _as_float(entertainer.get("current_rate")) or 350.0

    if profile_range:
        low, high = profile_range
        source = "profile_range"
    else:
        low = high = fallback_rate
        source = "current_rate"
    if low > high:
        low, high = high, low

    flex_low = _round_to_nearest_50(low * 0.9)
    flex_high = _round_to_nearest_50(high * 1.1)
    target = _round_to_nearest_50((low + high) / 2)
    return {
        "target_low": low,
        "target_high": high,
        "target": target,
        "flexible_min": flex_low,
        "flexible_max": flex_high,
        "source": source,
        "target_range_display": _money_range(low, high),
        "flex_range_display": _money_range(flex_low, flex_high),
        "floor_display": _format_rate(flex_low),
        "ceiling_display": _format_rate(flex_high),
    }


def conversation_completion_status(
    memory: dict[str, Any],
    analysis: dict[str, Any] | None = None,
    latest_reply: str | None = None,
) -> dict[str, Any]:
    """Decide whether Agent 2 should stop emailing this thread."""
    analysis = analysis or {}
    latest_reply = latest_reply or ""
    latest_lower = latest_reply.lower()
    response_type = str(analysis.get("response_type") or "").lower()
    has_date = bool(memory.get("date_mentions"))
    rate_ok = bool(memory.get("rate_is_acceptable"))
    below_range = bool(memory.get("rate_is_below_flexible_range"))
    requested_epk = bool(memory.get("requested_epk"))
    sent_epk = bool(memory.get("sent_epk"))
    materials_handled = not requested_epk or sent_epk
    logistics_known = memory.get("logistics_known") or {}
    known_logistics_count = sum(1 for value in logistics_known.values() if value)
    asks_direct_question = _latest_reply_needs_answer(latest_reply, memory)

    if response_type == "rejected":
        return {
            "stop_outreach": True,
            "outcome": "rejected",
            "reason": "Recipient declined or is not a fit. No further email should be sent.",
            "important_facts_count": 0,
        }

    important_facts_count = sum([
        1 if has_date else 0,
        1 if rate_ok else 0,
        1 if materials_handled else 0,
        min(known_logistics_count, 2),
    ])
    enough_booking_signal = response_type == "accepted" or (
        has_date
        and rate_ok
        and any(token in latest_lower for token in ["works", "confirmed", "book", "lock", "deal", "sounds good", "approved"])
    )
    stop = bool(
        enough_booking_signal
        and important_facts_count >= 3
        and not below_range
        and not asks_direct_question
    )
    return {
        "stop_outreach": stop,
        "outcome": "accepted" if stop else response_type or "open",
        "reason": (
            "Recipient has answered enough important booking details. Mark secured and stop emailing."
            if stop
            else "Thread still needs one concise answer or a core booking detail."
        ),
        "important_facts_count": important_facts_count,
        "has_date": has_date,
        "rate_ok": rate_ok,
        "materials_handled": materials_handled,
        "known_logistics_count": known_logistics_count,
        "asks_direct_question": asks_direct_question,
    }


def _normalize_pitch(pitch: dict[str, Any], entertainer: dict[str, Any], greeting: str | None = None) -> dict[str, str]:
    normalized = {**pitch}
    normalized["subject"] = remove_long_dashes(str(normalized.get("subject", "")))
    body = remove_long_dashes(str(normalized.get("body", "")))
    if greeting:
        body = ensure_greeting(body, greeting)
    normalized["body"] = _ensure_team_signoff(body, str(entertainer.get("name") or "The Artist"))
    return normalized


def remove_long_dashes(text: str | None) -> str:
    return str(text or "").replace("\u2014", "-").replace("\u2013", "-")


def team_name_for(name: str | None) -> str:
    artist_name = (name or "The Artist").strip() or "The Artist"
    suffix = "'" if artist_name.endswith("s") else "'s"
    return f"{artist_name}{suffix} Team"


def recipient_name_for(venue: dict[str, Any] | None, pitch: dict[str, Any] | None = None) -> str | None:
    venue = venue or {}
    pitch = pitch or {}
    contact_name = str(venue.get("contact_name") or venue.get("recipient_name") or "").strip()
    if contact_name and not _is_generic_contact_name(contact_name):
        return _title_words(contact_name)

    email = str(venue.get("contact_email") or pitch.get("recipient_email") or "").strip()
    if email and "@" in email:
        local = email.split("@", 1)[0].split("+", 1)[0]
        name_from_email = _name_from_email_local(local)
        if name_from_email:
            return name_from_email

    return None


def greeting_for(venue: dict[str, Any] | None, pitch: dict[str, Any] | None = None) -> str:
    recipient_name = recipient_name_for(venue, pitch)
    if recipient_name:
        return f"Hi {recipient_name},"
    venue_name = str(
        (venue or {}).get("name")
        or (venue or {}).get("venue_name")
        or (pitch or {}).get("venue_name")
        or ""
    ).strip()
    if venue_name:
        return f"Hi {venue_name} team,"
    return "Hi there,"


def ensure_greeting(body: str, greeting: str) -> str:
    clean = body.strip()
    if not clean:
        return greeting
    lines = clean.splitlines()
    first_idx = next((idx for idx, line in enumerate(lines) if line.strip()), None)
    if first_idx is None:
        return greeting
    first = lines[first_idx].strip()
    if re.match(r"^(hi|hey|hello|dear|what's up|whats up|what's good|whats good)\b", first, flags=re.I):
        lines[first_idx] = greeting
        return "\n".join(lines).strip()
    return f"{greeting}\n\n{clean}"


def reply_has_specific_date(text: str | None) -> bool:
    raw = str(text or "")
    lower = raw.lower()
    if _extract_date_mentions(raw):
        return True
    return bool(re.search(r"\b\d{1,2}(:\d{2})?\s*(am|pm)\b", lower))


def _extract_date_mentions(text: str | None) -> list[str]:
    raw = str(text or "")
    patterns = [
        r"\b(?:jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|sept|september|oct|october|nov|november|dec|december)\.?\s+\d{1,2}(?:st|nd|rd|th)?(?:,\s*\d{4})?\b",
        r"\b\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b",
        r"\b(?:this|next)\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
        r"\b(?:today|tomorrow|tonight)\b",
        r"\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+(?:at\s+)?\d{1,2}(?::\d{2})?\s*(?:am|pm)\b",
    ]
    mentions: list[str] = []
    for pattern in patterns:
        mentions.extend(match.group(0).strip() for match in re.finditer(pattern, raw, flags=re.I))
    return mentions


def _extract_money_mentions(text: str | None) -> list[str]:
    raw = str(text or "")
    amounts = [f"${match.group(1)}" for match in re.finditer(r"\$\s*([0-9][0-9,]*(?:\.\d{1,2})?)", raw)]
    return _unique_preserve_order(amounts)


def _extract_money_values(text: str | None) -> list[float]:
    raw = str(text or "")
    values: list[float] = []
    for match in re.finditer(r"\$\s*([0-9][0-9,]*(?:\.\d{1,2})?)", raw):
        amount = _as_float(match.group(1).replace(",", ""))
        if amount is not None:
            values.append(amount)
    return values


def _extract_rate_range(*texts: str) -> tuple[float, float] | None:
    combined = "\n".join(text for text in texts if text)
    dollar_patterns = [
        r"\$\s*([0-9][0-9,]*(?:\.\d{1,2})?)\s*(?:-|to|through|and)\s*\$?\s*([0-9][0-9,]*(?:\.\d{1,2})?)",
        r"(?:rate|price|pricing|budget|range)[^\n$0-9]{0,30}\$?\s*([0-9][0-9,]*(?:\.\d{1,2})?)\s*(?:-|to|through|and)\s*\$?\s*([0-9][0-9,]*(?:\.\d{1,2})?)",
    ]
    for pattern in dollar_patterns:
        match = re.search(pattern, combined, flags=re.I)
        if not match:
            continue
        low = _as_float(match.group(1).replace(",", ""))
        high = _as_float(match.group(2).replace(",", ""))
        if low is not None and high is not None and low >= 50 and high >= 50:
            return low, high
    return None


def _rate_status(value: Any, policy: dict[str, Any]) -> dict[str, Any]:
    amount = _as_float(value)
    if amount is None:
        return {
            "acceptable": True,
            "within_range": False,
            "below_range": False,
            "above_range": False,
            "guidance": "No venue counter detected; use the proposed or current rate.",
        }

    floor = float(policy.get("flexible_min") or 0)
    ceiling = float(policy.get("flexible_max") or amount)
    below = amount < floor
    above = amount > ceiling
    within = floor <= amount <= ceiling
    if below:
        guidance = f"Venue counter {_format_rate(amount)} is below the acceptable floor. Counter at {policy.get('floor_display') or _format_rate(floor)}."
    elif within:
        guidance = f"Venue counter {_format_rate(amount)} is inside the flexible range and can be accepted."
    else:
        guidance = f"Venue counter {_format_rate(amount)} is above the target ceiling, so it can be accepted."
    return {
        "acceptable": not below,
        "within_range": within,
        "below_range": below,
        "above_range": above,
        "guidance": guidance,
    }


def _latest_reply_needs_answer(latest_reply: str | None, memory: dict[str, Any]) -> bool:
    text = str(latest_reply or "")
    lower = text.lower()
    if "?" not in text:
        return False
    if memory.get("rate_is_below_flexible_range"):
        return True
    blocker_terms = [
        "can you",
        "could you",
        "would you",
        "does that work",
        "is that okay",
        "available",
        "availability",
        "rate",
        "price",
        "budget",
        "cost",
        "fee",
        "epk",
        "reel",
        "press kit",
        "invoice",
        "contract",
        "load",
        "soundcheck",
        "set time",
        "set length",
    ]
    return any(term in lower for term in blocker_terms)


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value).replace(",", "").replace("$", "").strip())
    except (TypeError, ValueError):
        return None


def _round_to_nearest_50(value: float) -> int:
    return int(math.floor((float(value) / 50) + 0.5) * 50)


def _money_range(low: Any, high: Any) -> str:
    low_display = _format_rate(low) or "$0"
    high_display = _format_rate(high) or low_display
    return low_display if low_display == high_display else f"{low_display}-{high_display}"


def _unique_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


def _latest(values: list[Any]) -> Any | None:
    return values[-1] if values else None


def _format_rate(value: Any) -> str | None:
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return None
    return f"${amount:.0f}"


def _compact_text(value: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", value).strip()
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def _logistics_question(missing: list[str]) -> str:
    if not missing:
        return ""
    if len(missing) == 1:
        return f"Could you send the {missing[0]} when you have it?"
    return f"Could you send the {missing[0]} and {missing[1]} when you have them?"


def _is_generic_contact_name(name: str) -> bool:
    lowered = re.sub(r"[^a-z0-9 ]+", " ", name.lower()).strip()
    return lowered in {
        "booking team",
        "demo booking team",
        "events team",
        "team",
        "contact",
        "info",
        "booking",
        "bookings",
    }


def _title_words(value: str) -> str:
    return " ".join(part.capitalize() for part in re.split(r"\s+", value.strip()) if part)


def _name_from_email_local(local: str) -> str | None:
    cleaned = re.sub(r"\d+", "", local.lower())
    parts = [part for part in re.split(r"[._\-]+", cleaned) if part]
    generic = {"info", "hello", "contact", "booking", "bookings", "events", "team", "admin", "noreply", "no", "reply"}
    if not parts or all(part in generic for part in parts):
        return None
    if len(parts) == 1:
        token = parts[0]
        suffixes = ["benches", "events", "booking", "bookings", "productions", "collective", "agency", "records", "music", "campus", "team"]
        for suffix in suffixes:
            if token.endswith(suffix) and len(token) > len(suffix) + 2:
                return f"{token[:-len(suffix)].capitalize()} {suffix.capitalize()}"
    return " ".join(part.capitalize() for part in parts)


def ensure_team_signoff(body: str, artist_name: str) -> str:
    team_name = team_name_for(artist_name)
    clean = body.strip()
    expected = f"Sincerely,\n{team_name}"
    if clean.endswith(expected):
        return clean

    lines = clean.splitlines()
    while lines and not lines[-1].strip():
        lines.pop()

    lower_artist = artist_name.lower()
    lower_team = team_name.lower()
    signoff_words = {"best", "thanks", "thank you", "sincerely", "regards", "cheers"}
    for idx in range(len(lines) - 1, max(-1, len(lines) - 5), -1):
        candidate = lines[idx].strip().strip("- ").rstrip(",").lower()
        if candidate in signoff_words:
            lines = lines[:idx]
            break

    while lines:
        last = lines[-1].strip()
        last_clean = last.strip("- ").rstrip(",").lower()
        if last_clean in {lower_artist, lower_team} or last_clean in signoff_words:
            lines.pop()
            continue
        break

    return "\n".join(lines).rstrip() + f"\n\nSincerely,\n{team_name}"


_ensure_team_signoff = ensure_team_signoff


def _fallback_pitch(entertainer: dict[str, Any], venue: dict[str, Any], rate: float) -> dict[str, str]:
    name = entertainer.get("name", "The Artist")
    team_name = team_name_for(name)
    etype = entertainer.get("type", "performer")
    genre = entertainer.get("genre", "")
    exp = entertainer.get("experience_years", 2)
    followers = entertainer.get("social_followers", 5000)
    location = entertainer.get("location", "LA")
    venue_name = venue.get("name", "your venue")
    venue_type = (venue.get("venue_type") or "").lower()
    why_fits = (venue.get("why_fits") or "").strip()
    venue_context = (
        f"\n\nYour programming stood out because {why_fits.rstrip('.')}. That lines up with the rooms we are targeting right now."
        if why_fits
        else ""
    )

    idx = int(hashlib.md5(f"{name}{venue_name}".encode()).hexdigest(), 16) % 3

    if etype.lower() == "rapper":
        if "college" in venue_type or "university" in venue_type or "campus" in venue_type:
            subjects = [
                f"{name} for {venue_name} campus programming",
                f"Hip-hop set for {venue_name} students",
                f"{name} | campus performance inquiry",
            ]
            bodies = [
                f"Hey {venue_name} team,\n\nWe represent {name}, a rapper out of {location} making high-energy hip-hop for college crowds. He has been performing for {exp} years and has {followers:,} followers across socials.{venue_context}\n\nOur team can bring a tight 30-minute set, promote the event hard, and keep the show student-friendly without losing the energy. His usual rate is ${rate:.0f}/show, and we can stay flexible if there is a student board budget to work around.\n\nCould we send over a reel for an upcoming campus slot?\n\nSincerely,\n{team_name}",
                f"What's up {venue_name},\n\nWe are booking campus shows for {name}, a hip-hop artist building toward more student-facing performances this year. The goal is simple: play rooms where students actually discover new artists, not just background sets.{venue_context}\n\nHe brings a crowd-interactive set, clean versions when needed, and promo support to {followers:,} followers. Rate is ${rate:.0f}/show.\n\nIs there a programming slot this semester where he might make sense?\n\nSincerely,\n{team_name}",
                f"Hi {venue_name} team,\n\nWe are reaching out because your campus audience feels aligned with {name}'s live show. He is a {genre or 'hip-hop'} artist from {location} with {exp} years of live experience and {followers:,} social followers.{venue_context}\n\nHis set is built for student energy: hooks, call-and-response moments, and an easy 30-45 minute format. Rate is ${rate:.0f}/show.\n\nHappy to send music and a short performance reel.\n\nSincerely,\n{team_name}",
            ]
        elif "festival" in venue_type:
            subjects = [
                f"{name} festival performance inquiry",
                f"Hip-hop artist submission for {venue_name}",
                f"{name} | emerging-stage booking request",
            ]
            bodies = [
                f"Hi {venue_name} team,\n\nWe represent {name}, a rapper from {location}, and would love to submit him for an emerging hip-hop slot. He has {followers:,} followers, {exp} years of live experience, and a set built to catch people walking between stages.{venue_context}\n\nHe can do 20, 30, or 45 minutes. Our team can push the appearance across Instagram/TikTok/YouTube and keep production simple. Rate is ${rate:.0f}/show depending on slot.\n\nCan we send over his EPK and reel?\n\nSincerely,\n{team_name}",
                f"Hey {venue_name},\n\nWe are submitting {name}, an independent hip-hop artist from {location}, for a performance slot. We are specifically chasing festival looks because they line up with his goal of reaching new audiences this year.{venue_context}\n\nHis live set is high-momentum, crowd-facing, and easy to drop into a showcase lineup. Current rate is ${rate:.0f}, flexible by stage and set length.\n\nWould love for him to be considered.\n\nSincerely,\n{team_name}",
                f"Hello {venue_name} booking team,\n\nWe work with {name}, a {genre or 'hip-hop'} artist from {location}. He has {followers:,} social followers and a live show shaped for festival crowds: quick hooks, strong transitions, and direct audience engagement.{venue_context}\n\nHe is available for opener, showcase, or emerging-stage slots. Rate is ${rate:.0f}/show, and we can send a clean EPK today.\n\nSincerely,\n{team_name}",
            ]
        elif "bar" in venue_type or "nightlife" in venue_type or "nightclub" in venue_type:
            subjects = [
                f"{name} hip-hop night at {venue_name}",
                f"Booking inquiry for {name} at {venue_name}",
                f"{name} | live set for {venue_name}",
            ]
            bodies = [
                f"Hey {venue_name},\n\nWe represent {name}, a rapper from {location}, and we are looking for bar rooms where a hip-hop set can actually lift the night instead of feeling tacked on.{venue_context}\n\nHe has {followers:,} followers, promotes every booking, and can bring a 25-35 minute set that works before a DJ, between acts, or as a feature slot. Rate is around ${rate:.0f}, flexible by night.\n\nCould we make a date work?\n\nSincerely,\n{team_name}",
                f"Hi {venue_name} team,\n\nThe room feels right for {name}, so we wanted to reach out directly. He is a {genre or 'hip-hop'} artist out of {location}, with {exp} years performing and a growing college-age following.{venue_context}\n\nOur team can help draw, keep the energy up, and make the promo easy for your team. Rate is ${rate:.0f}/night.\n\nOpen to trying a weekend or showcase slot?\n\nSincerely,\n{team_name}",
                f"What's good {venue_name},\n\nWe are booking {name}, an LA rapper looking for bars and music rooms in the $300-400 range. We are trying to stack consistent shows that build real audience, and your crowd feels like a strong match.{venue_context}\n\nHe brings a tight live set, social promo to {followers:,} followers, and a flexible format. Let us know if you have a date that needs hip-hop energy.\n\nSincerely,\n{team_name}",
            ]
        else:
            subjects = [
                f"{name} booking inquiry for {venue_name}",
                f"{name} hip-hop set for {venue_name}",
                f"Rapper booking request: {name}",
            ]
            bodies = [
                f"Hi {venue_name} booking team,\n\nWe represent {name}, an independent rapper from {location}. We are reaching out because your stage feels like the right next step for his live show.{venue_context}\n\nHe brings a polished 30-45 minute set, promotes to {followers:,} followers, and keeps the ask straightforward: ${rate:.0f}/show, flexible if it helps build the bill.\n\nCould we send his reel and a few date options?\n\nSincerely,\n{team_name}",
                f"Hey {venue_name},\n\nWe are booking {name}, a hip-hop artist out of {location}. He has spent {exp} years building a live set that works in real music rooms, not just online clips.{venue_context}\n\nThe show is high-energy, easy to slot with other local acts, and backed by promo to {followers:,} followers. Rate is ${rate:.0f}, but our team cares most about finding the right bill.\n\nWorth a quick conversation?\n\nSincerely,\n{team_name}",
                f"Hi there,\n\nWe are reaching out about booking {venue_name}. We represent {name}, a {genre or 'hip-hop'} artist from {location}, focused on campuses, music venues, festivals, and bars this year.{venue_context}\n\nHe does tight 30-45 minute sets with strong stage presence and active pre-show promo. Rate is ${rate:.0f}/show.\n\nLet us know if we should send over the EPK.\n\nSincerely,\n{team_name}",
            ]
    else:
        subjects = [
            f"{name} booking inquiry for {venue_name}",
            f"{name} available for {venue_name}",
            f"Performance booking: {name} at {venue_name}",
        ]
        bodies = [
            f"Hi {venue_name} team,\n\nWe represent {name}, a {genre} {etype} based in {location} with {exp} years performing and {followers:,} social followers.{venue_context}\n\nWe would love to explore a show that fits your room and audience. His rate is ${rate:.0f}/show, and our team is happy to discuss the right format.\n\nWorth a quick call?\n\nSincerely,\n{team_name}",
            f"Hello {venue_name},\n\nWe are booking {name}, a {etype} focused on {genre or 'live performance'}. Your programming feels aligned with the kind of audience he is trying to reach.{venue_context}\n\nHe has {exp} years on stage, {followers:,} followers, and a flexible set format. Current rate is ${rate:.0f}/show.\n\nCould we send more details?\n\nSincerely,\n{team_name}",
            f"Hi there,\n\nWe represent {name}, a {etype} from {location}. We are putting together dates with venues and organizations where the audience match is strong.{venue_context}\n\nHis performance rate is ${rate:.0f}/show, and we can send a short reel, references, and possible dates.\n\nSincerely,\n{team_name}",
        ]

    return {"subject": subjects[idx], "body": bodies[idx]}


def _fallback_reply_draft(
    entertainer: dict[str, Any],
    venue: dict[str, Any],
    pitch: dict[str, Any],
    latest_reply: str,
    analysis: dict[str, Any],
    memory: dict[str, Any],
    prior_context: str | None = None,
) -> dict[str, str]:
    name = entertainer.get("name", "The Artist")
    team_name = team_name_for(name)
    venue_name = venue.get("name") or pitch.get("venue_name") or "your team"
    rate = memory.get("agreed_rate") or _format_rate(pitch.get("proposed_rate") or entertainer.get("current_rate")) or "$350"
    policy = memory.get("price_policy") or price_policy_for(entertainer, pitch)
    floor_rate = policy.get("floor_display") or rate
    response_type = (analysis.get("response_type") or "").lower()
    reply_lower = (latest_reply or "").lower()
    has_date = bool(memory.get("latest_reply_dates") or memory.get("date_mentions") or reply_has_specific_date(latest_reply))
    if memory.get("rate_is_below_flexible_range"):
        rate_phrase = f"we cannot make {rate}/show work, but we can come down to {floor_rate}/show if the date and set format are locked"
    elif memory.get("rate_from_thread"):
        rate_phrase = f"we can make {rate}/show work as discussed"
    else:
        rate_phrase = f"his current rate is {rate}/show"
    missing = memory.get("missing_logistics") or []
    primary_missing = [item for item in missing if item in {"set time", "load-in"}] or missing[:2]
    logistics_question = _logistics_question(primary_missing)
    subject = pitch.get("pitch_subject") or f"Booking inquiry for {name}"
    if not str(subject).lower().startswith("re:"):
        subject = f"Re: {subject}"
    relationship_line = (
        f"\n\nWe also have the previous {venue_name} booking notes on file, so we will keep this consistent with what your team has already shared."
        if prior_context and str(prior_context).strip()
        else ""
    )

    if memory.get("rate_is_below_flexible_range"):
        body = f"Hi {venue_name} team,\n\nThanks for being clear on budget. For {name}, {rate_phrase}.\n\nIf that works on your end, we can keep the next step simple and lock the remaining logistics.\n\nSincerely,\n{team_name}"
    elif has_date:
        epk_line = "We can send the EPK/reel over as well." if memory.get("requested_epk") and not memory.get("sent_epk") else ""
        body = f"Hi {venue_name} team,\n\nThanks for sending that over. We have the date noted for {name}, and {rate_phrase}.\n\n{epk_line}{' ' if epk_line and logistics_question else ''}{logistics_question}\n\nSincerely,\n{team_name}"
    elif response_type == "accepted" or any(word in reply_lower for word in ["love", "interested", "available", "book"]):
        body = f"Hi {venue_name} team,\n\nThanks for getting back to us. We'd love to move this forward for {name}.{relationship_line}\n\nWe can keep the rate at {rate}/show. {logistics_question or 'We can send over the EPK and a couple of date options if helpful.'}\n\nSincerely,\n{team_name}"
    elif response_type == "negotiating" or any(word in reply_lower for word in ["budget", "rate", "price", "cost", "$"]):
        body = f"Hi {venue_name} team,\n\nThanks for the note. For {name}, {rate_phrase}.\n\nIf that still works on your end, {logistics_question.lower() if logistics_question else 'we can move into logistics next.'}\n\nSincerely,\n{team_name}"
    elif response_type == "rejected":
        body = f"Hi {venue_name} team,\n\nThanks for letting us know. We appreciate you taking a look at {name}.\n\nLet us know if you are interested in a future date or if a performance slot opens up later in the season.\n\nSincerely,\n{team_name}"
    else:
        body = f"Hi {venue_name} team,\n\nThanks for getting back to us. Happy to share more on {name}: he brings a tight live set, active promo support, and a format that can flex for your room.\n\nWe can keep the rate at {rate}/show. {logistics_question or 'Would a reel or EPK be helpful as the next step?'}\n\nSincerely,\n{team_name}"

    return {"subject": subject, "body": body}


def _fallback_rebook_pitch(
    entertainer: dict[str, Any],
    booking: dict[str, Any],
    rate: float,
    prior_context: str | None = None,
) -> dict[str, str]:
    name = entertainer.get("name", "The Artist")
    team_name = team_name_for(name)
    venue_name = booking.get("venue_name") or "your venue"
    summary = (booking.get("show_summary") or "").strip()
    context = (
        f"\n\nThe previous show notes were: {summary.rstrip('.')}. That is the kind of momentum we would like to build on."
        if summary
        else "\n\nThe last booking felt like a strong fit, and our team would love to build on that momentum with a fresh set."
    )
    history_line = (
        "\n\nWe reviewed the previous thread so we can keep the rate, logistics, and tone consistent with what your team already shared."
        if prior_context and str(prior_context).strip()
        else ""
    )
    subject = f"Rebooking {name} at {venue_name}"
    body = (
        f"Hi {venue_name} team,\n\n"
        f"Thanks again for working with {name}.{context}{history_line}\n\n"
        f"Would you be open to bringing him back for another date? We can share updated material, a short promo plan, "
        f"and a few available windows. We can also stay around the previous ${rate:.0f}/show range if that still works for your programming.\n\n"
        f"Sincerely,\n{team_name}"
    )
    return {"subject": subject, "body": body}
