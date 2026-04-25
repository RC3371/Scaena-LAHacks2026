"""
Agent 4: Follow-Up, Objection Handling & Re-engagement
Generates follow-up sequences and handles objections automatically.
"""

import json
import os
from datetime import datetime, timedelta
import anthropic
from database import get_db, rows_to_list, row_to_dict

_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
_simulation_mode = not _api_key or _api_key == "simulation"
client = anthropic.Anthropic(api_key=_api_key or "sk-ant-placeholder") if not _simulation_mode else None

FOLLOWUP_DELAYS = {1: 3, 2: 7, 3: 14}

_MOCK_FOLLOWUP_TEMPLATES = {
    1: {
        "subject": "Re: Booking Inquiry – Wanted to share my latest set",
        "body": (
            "Hey {contact},\n\n"
            "I performed to a sold-out crowd last weekend and clipped the best 3 minutes — "
            "thought you might enjoy it: {youtube}\n\n"
            "Audiences went wild for it. I have openings in the next 4 weeks and would love to bring "
            "this energy to {venue}.\n\nBest, {name}"
        ),
        "angle_used": "share a performance video or recent success",
    },
    2: {
        "subject": "Re: Booking – Quick question for you",
        "body": (
            "Hi {contact},\n\n"
            "Just circling back — I've had 3 shows since I first reached out and every one sold out. "
            "Audience reviews have been incredible: 'best set of the night,' 'had us in tears laughing.'\n\n"
            "Is {venue} booking for next month? I'm available at ${rate}/show and flexible on dates.\n\nBest, {name}"
        ),
        "angle_used": "highlight audience feedback and social proof",
    },
    3: {
        "subject": "Last note – Available for {venue} this month",
        "body": (
            "Hey {contact},\n\n"
            "One last note — I have 2 openings left in {month} and wanted to give {venue} first right of refusal. "
            "After these fill up I'll be booking out to next quarter.\n\n"
            "If the timing ever works, I'd love to be on your stage. No pressure either way.\n\nBest, {name}"
        ),
        "angle_used": "create urgency with availability for upcoming dates",
    },
}


def _mock_followup(profile: dict, prospect: dict, original_pitch: dict, sequence_number: int) -> dict:
    import calendar
    month_name = calendar.month_name[(datetime.now().month % 12) + 1]
    template = _MOCK_FOLLOWUP_TEMPLATES.get(sequence_number, _MOCK_FOLLOWUP_TEMPLATES[3])
    body = template["body"].format(
        contact=prospect.get("contact_name", "there"),
        youtube=profile.get("youtube_url", "available on request"),
        venue=prospect.get("name", "your venue"),
        name=profile.get("name", "there"),
        rate=int(profile.get("rate_max", 400)),
        month=month_name,
    )
    subject = template["subject"].format(venue=prospect.get("name", "your venue"))
    return {"subject": subject, "body": body, "angle_used": template["angle_used"]}

FOLLOWUP_ANGLES = {
    1: "share a performance video or recent success",
    2: "highlight audience feedback and social proof",
    3: "create urgency with availability for upcoming dates",
}


def generate_followup_message(profile: dict, prospect: dict, original_pitch: dict, sequence_number: int, analytics_insights: dict = None) -> dict:
    if _simulation_mode:
        return _mock_followup(profile, prospect, original_pitch, sequence_number)

    angle = FOLLOWUP_ANGLES.get(sequence_number, "general check-in")
    days_since = FOLLOWUP_DELAYS.get(sequence_number, 14)

    performance_note = ""
    if analytics_insights and analytics_insights.get("effective_angles"):
        best_angle = analytics_insights["effective_angles"][0] if analytics_insights["effective_angles"] else ""
        performance_note = f"\nData shows this angle converts best: {best_angle}"

    prompt = f"""You are an expert entertainment booking agent. Write follow-up #{sequence_number} from {profile['name']} to {prospect['name']}.

CONTEXT:
- This is day {days_since} since the original pitch was sent
- The venue has not responded yet
- Follow-up angle to use: {angle}
{performance_note}

PERFORMER: {profile['name']} ({profile.get('entertainer_type', 'performer')})
- Experience: {profile.get('experience_years', 0)} years, {profile.get('shows_count', 0)}+ shows
- Instagram: {profile.get('instagram_followers', 0):,} followers
- Rate: ${profile.get('rate_min', 0)}-${profile.get('rate_max', 0)}/show
- YouTube: {profile.get('youtube_url', 'Available upon request')}

VENUE: {prospect['name']} ({prospect.get('type', 'venue')}) in {prospect.get('location', 'your area')}
Contact: {prospect.get('contact_name', 'Booking Manager')}

ORIGINAL PITCH SUBJECT: {original_pitch.get('subject', 'Booking Inquiry')}

Write a follow-up that:
1. Is clearly different from the initial pitch (different angle, different hook)
2. Adds NEW value — don't just say "following up on my previous email"
3. For sequence {sequence_number}: {angle}
4. Is shorter than the original (75-125 words)
5. Ends with a specific, easy call-to-action

Return JSON:
{{
  "subject": "Re: [subject] or new subject that stands out",
  "body": "follow-up email body",
  "angle_used": "{angle}"
}}

Return ONLY the JSON."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    return json.loads(raw)


def generate_objection_response(profile: dict, prospect: dict, objection_type: str, objection_text: str, original_rate: float) -> dict:
    prompt = f"""You are an expert entertainment booking negotiator. Generate 2 counter-offer responses to this objection.

PERFORMER: {profile['name']} ({profile.get('entertainer_type', 'performer')})
VENUE: {prospect['name']}
ORIGINAL RATE: ${original_rate}/show

OBJECTION TYPE: {objection_type}
OBJECTION TEXT: "{objection_text}"

Generate 2 different counter-offer strategies:
1. Reduced rate offer (slight discount for relationship building)
2. Alternative structure (revenue share, or value-add like bringing your own crowd)

Return JSON:
{{
  "counter_offers": [
    {{
      "strategy": "reduced rate",
      "subject": "email subject",
      "body": "counter-offer email body (100-150 words)",
      "proposed_terms": "specific terms offered"
    }},
    {{
      "strategy": "alternative structure",
      "subject": "email subject",
      "body": "counter-offer email body (100-150 words)",
      "proposed_terms": "specific terms offered"
    }}
  ],
  "recommended_strategy": "which counter-offer to use and why"
}}

Return ONLY the JSON."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    return json.loads(raw)


def schedule_followups_for_profile(profile_id: int) -> list:
    """Find pitches that need follow-ups scheduled and create them."""
    with get_db() as conn:
        profile = row_to_dict(conn.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,)).fetchone())

        pitches = rows_to_list(conn.execute(
            "SELECT * FROM pitches WHERE profile_id = ? AND status = 'sent'", (profile_id,)
        ).fetchall())

        existing_followups = rows_to_list(conn.execute(
            "SELECT * FROM follow_ups WHERE profile_id = ?", (profile_id,)
        ).fetchall())

        responses = rows_to_list(conn.execute(
            """SELECT pr.pitch_id FROM pitch_responses pr
               JOIN pitches p ON pr.pitch_id = p.id
               WHERE p.profile_id = ?""",
            (profile_id,)
        ).fetchall())

        responded_pitch_ids = {r["pitch_id"] for r in responses}

        analytics_insights = None
        latest_snapshot = row_to_dict(conn.execute(
            "SELECT * FROM analytics_snapshots WHERE profile_id = ? ORDER BY created_at DESC LIMIT 1",
            (profile_id,)
        ).fetchone())
        if latest_snapshot:
            try:
                snapshot_data = json.loads(latest_snapshot["snapshot_data"])
                analytics_insights = snapshot_data.get("ai_insights")
            except Exception:
                pass

    scheduled = []
    for pitch in pitches:
        if pitch["id"] in responded_pitch_ids:
            continue

        completed_seqs = {f["sequence_number"] for f in existing_followups if f["pitch_id"] == pitch["id"] and f["status"] in ("sent", "scheduled")}
        next_seq = 1
        while next_seq in completed_seqs:
            next_seq += 1

        if next_seq > 3:
            continue

        sent_at = datetime.fromisoformat(pitch["sent_at"]) if pitch.get("sent_at") else datetime.now()
        delay_days = FOLLOWUP_DELAYS.get(next_seq, 14)
        scheduled_for = sent_at + timedelta(days=delay_days)

        with get_db() as conn:
            prospect = row_to_dict(conn.execute("SELECT * FROM prospects WHERE id = ?", (pitch["prospect_id"],)).fetchone())

        if not prospect:
            continue

        try:
            followup_content = generate_followup_message(
                profile, prospect, pitch, next_seq, analytics_insights
            )
        except Exception as e:
            followup_content = {
                "subject": f"Following up – {prospect['name']}",
                "body": f"Hi {prospect.get('contact_name', 'there')},\n\nJust checking in on my previous note. I'd love the opportunity to perform at {prospect['name']}. Please let me know if you have any questions.\n\nBest,\n{profile['name']}",
                "angle_used": FOLLOWUP_ANGLES.get(next_seq, "general"),
            }

        with get_db() as conn:
            cursor = conn.execute(
                """INSERT INTO follow_ups (pitch_id, prospect_id, profile_id, sequence_number, subject, body, scheduled_for, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 'scheduled')""",
                (pitch["id"], pitch["prospect_id"], profile_id, next_seq,
                 followup_content["subject"], followup_content["body"],
                 scheduled_for.isoformat()),
            )
            followup_id = cursor.lastrowid

        scheduled.append({
            "id": followup_id,
            "pitch_id": pitch["id"],
            "prospect_id": pitch["prospect_id"],
            "prospect_name": prospect["name"],
            "sequence_number": next_seq,
            "scheduled_for": scheduled_for.isoformat(),
            "subject": followup_content["subject"],
        })

    return scheduled
