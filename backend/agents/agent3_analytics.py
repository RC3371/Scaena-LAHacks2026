"""
Agent 3: Tracking, Learning & Optimization
Analyzes booking responses and recommends strategy adjustments.
"""

import json
import os
from collections import defaultdict
import anthropic
from database import get_db, rows_to_list

_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
_simulation_mode = not _api_key or _api_key == "simulation"
client = anthropic.Anthropic(api_key=_api_key or "sk-ant-placeholder") if not _simulation_mode else None


def compute_analytics(profile_id: int) -> dict:
    """Compute full analytics for a profile by analyzing all pitches and responses."""
    with get_db() as conn:
        pitches = rows_to_list(conn.execute(
            "SELECT * FROM pitches WHERE profile_id = ?", (profile_id,)
        ).fetchall())

        responses = rows_to_list(conn.execute(
            """SELECT pr.*, p.type as venue_type, p.name as venue_name
               FROM pitch_responses pr
               JOIN prospects p ON pr.prospect_id = p.id
               WHERE p.profile_id = ?""",
            (profile_id,)
        ).fetchall())

        prospects = rows_to_list(conn.execute(
            "SELECT * FROM prospects WHERE profile_id = ?", (profile_id,)
        ).fetchall())

        follow_ups = rows_to_list(conn.execute(
            "SELECT * FROM follow_ups WHERE profile_id = ?", (profile_id,)
        ).fetchall())

    total_pitches = len([p for p in pitches if p["status"] == "sent"])
    total_responses = len(responses)
    overall_response_rate = (total_responses / total_pitches * 100) if total_pitches > 0 else 0

    by_venue_type = defaultdict(lambda: {"sent": 0, "responses": 0, "bookings": 0, "response_types": defaultdict(int)})
    for p in pitches:
        if p["status"] == "sent":
            venue = next((pr for pr in prospects if pr["id"] == p["prospect_id"]), None)
            if venue:
                by_venue_type[venue["type"]]["sent"] += 1

    for r in responses:
        vtype = r.get("venue_type", "Unknown")
        by_venue_type[vtype]["responses"] += 1
        by_venue_type[vtype]["response_types"][r["response_type"]] += 1
        if r["response_type"] == "booked":
            by_venue_type[vtype]["bookings"] += 1

    venue_performance = {}
    for vtype, data in by_venue_type.items():
        sent = data["sent"]
        resp = data["responses"]
        venue_performance[vtype] = {
            "sent": sent,
            "responses": resp,
            "bookings": data["bookings"],
            "response_rate": round((resp / sent * 100) if sent > 0 else 0, 1),
            "booking_rate": round((data["bookings"] / sent * 100) if sent > 0 else 0, 1),
            "response_types": dict(data["response_types"]),
        }

    response_type_counts = defaultdict(int)
    for r in responses:
        response_type_counts[r["response_type"]] += 1

    booked_count = response_type_counts.get("booked", 0)
    interested_count = response_type_counts.get("interested", 0)
    negotiating_count = response_type_counts.get("negotiating", 0)

    accepted_rates = [p["proposed_rate"] for p in pitches if p["status"] == "sent" and p["proposed_rate"] > 0]
    avg_proposed_rate = sum(accepted_rates) / len(accepted_rates) if accepted_rates else 0

    followup_sent = len([f for f in follow_ups if f["status"] == "sent"])
    followup_responses = len([r for r in responses if any(
        f["pitch_id"] == r["pitch_id"] and f["status"] == "sent" for f in follow_ups
    )])

    pending_followups = []
    for p in pitches:
        if p["status"] == "sent":
            has_response = any(r["pitch_id"] == p["id"] for r in responses)
            if not has_response:
                existing_followups = [f for f in follow_ups if f["pitch_id"] == p["id"]]
                next_seq = len(existing_followups) + 1
                if next_seq <= 3:
                    pending_followups.append({
                        "pitch_id": p["id"],
                        "sequence": next_seq,
                        "prospect_id": p["prospect_id"],
                    })

    analytics = {
        "summary": {
            "total_prospects": len(prospects),
            "total_pitches_sent": total_pitches,
            "total_responses": total_responses,
            "overall_response_rate": round(overall_response_rate, 1),
            "total_bookings": booked_count,
            "interested_leads": interested_count + negotiating_count,
            "avg_proposed_rate": round(avg_proposed_rate, 0),
            "follow_ups_sent": followup_sent,
        },
        "venue_performance": venue_performance,
        "response_breakdown": dict(response_type_counts),
        "pending_followups_count": len(pending_followups),
        "top_performing_venue_types": sorted(
            [(k, v["response_rate"]) for k, v in venue_performance.items() if v["sent"] > 0],
            key=lambda x: x[1],
            reverse=True,
        )[:3],
    }

    if total_pitches >= 3:
        if _simulation_mode:
            insights = _mock_ai_insights(analytics, venue_performance, booked_count, avg_proposed_rate)
        else:
            insights = _generate_ai_insights(analytics, venue_performance, booked_count, avg_proposed_rate)
        analytics["ai_insights"] = insights

    return analytics


def _mock_ai_insights(analytics: dict, venue_performance: dict, booked_count: int, avg_rate: float) -> dict:
    best_type = max(venue_performance.items(), key=lambda x: x[1]["response_rate"], default=(None, {}))[0] if venue_performance else "Comedy Club"
    worst_type = min(venue_performance.items(), key=lambda x: x[1]["response_rate"], default=(None, {}))[0] if venue_performance else "Festival"
    rate = analytics["summary"].get("overall_response_rate", 0)
    return {
        "top_insight": f"{best_type}s are converting at {rate}% — double down on this channel for maximum bookings.",
        "effective_angles": [
            "Share a recent performance video in the first line",
            "Reference specific acts the venue has booked recently",
            "Lead with audience size + show count as social proof",
        ],
        "recommendations": [
            {"action": f"Focus next round on {best_type}s — highest response rate in your data", "expected_impact": "+20% overall bookings", "priority": "high"},
            {"action": f"Raise rate to ${avg_rate * 1.1:.0f} — venues are accepting current rate without negotiation", "expected_impact": "+10% revenue per show", "priority": "high"},
            {"action": f"Reduce outreach to {worst_type}s until you have more social proof", "expected_impact": "Better ROI on pitch time", "priority": "medium"},
        ],
        "rate_analysis": {
            "current_rate_assessment": "slightly below market",
            "suggested_adjustment": f"Raise to ${avg_rate * 1.1:.0f} base — data shows 80%+ acceptance at current rate",
            "reasoning": "High acceptance rate signals you have room to increase without losing bookings.",
        },
        "focus_channels": [best_type, "College Venue"],
        "warning_flags": [f"{worst_type} response rate is low — personalize these pitches more before next round"],
    }


def _generate_ai_insights(analytics: dict, venue_performance: dict, booked_count: int, avg_rate: float) -> dict:
    prompt = f"""You are an entertainment booking strategy expert. Analyze this booking campaign data and provide actionable insights.

CAMPAIGN DATA:
- Total pitches sent: {analytics['summary']['total_pitches_sent']}
- Overall response rate: {analytics['summary']['overall_response_rate']}%
- Total bookings: {booked_count}
- Average proposed rate: ${avg_rate}

VENUE PERFORMANCE:
{json.dumps(venue_performance, indent=2)}

Return a JSON object with this structure:
{{
  "top_insight": "the single most important finding",
  "effective_angles": ["angle1", "angle2", "angle3"],
  "recommendations": [
    {{
      "action": "...",
      "expected_impact": "...",
      "priority": "high/medium/low"
    }}
  ],
  "rate_analysis": {{
    "current_rate_assessment": "too low/market rate/above market",
    "suggested_adjustment": "...",
    "reasoning": "..."
  }},
  "focus_channels": ["best venue type 1", "best venue type 2"],
  "warning_flags": ["any concerning patterns"]
}}

Be specific and data-driven. Return ONLY the JSON."""

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
