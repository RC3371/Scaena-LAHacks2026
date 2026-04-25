"""
Agent 2: Personalized Initial Pitching
Generates customized, personalized pitch emails for each venue/opportunity.
"""

import json
import os
import anthropic

_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
_simulation_mode = not _api_key or _api_key == "simulation"
client = anthropic.Anthropic(api_key=_api_key or "sk-ant-placeholder") if not _simulation_mode else None


def _mock_pitch(profile: dict, prospect: dict, proposed_rate: float) -> dict:
    name = profile.get("name", "Your Name")
    etype = profile.get("entertainer_type", "performer").title()
    genre = profile.get("genre_style", "versatile style")
    years = profile.get("experience_years", 0)
    shows = profile.get("shows_count", 0)
    followers = profile.get("instagram_followers", 0)
    youtube = profile.get("youtube_url", "")
    contact = prospect.get("contact_name", "there")
    venue = prospect.get("name", "your venue")
    vtype = prospect.get("type", "venue")

    subject = f"Booking Inquiry – {name} ({etype}) | {venue}"
    body = (
        f"Hi {contact},\n\n"
        f"I came across {venue} and was immediately drawn to the energy you bring to your {vtype.lower()} — it's exactly the crowd I thrive with.\n\n"
        f"I'm {name}, a {etype.lower()} known for {genre}. Over {years} years I've built a following of {followers:,} on Instagram "
        f"and performed {shows}+ shows. Audiences consistently call my sets the highlight of the night.\n\n"
        f"{'Check out my recent performance: ' + youtube + chr(10) + chr(10) if youtube else ''}"
        f"I'd love to bring this energy to {venue}. I'm available at ${proposed_rate:.0f}/show and completely flexible on dates. "
        f"Would you be open to a quick 10-minute call this week?\n\n"
        f"Best,\n{name}"
    )
    return {"subject": subject, "body": body, "key_angle": f"Genre fit + {followers:,} followers social proof"}



def generate_pitch(profile: dict, prospect: dict, proposed_rate: float, analytics_insights: dict = None) -> dict:
    """Generate a single personalized pitch for a prospect."""
    if _simulation_mode:
        return _mock_pitch(profile, prospect, proposed_rate)

    social_proof_parts = []
    if profile.get("instagram_followers", 0) > 0:
        social_proof_parts.append(f"{profile['instagram_followers']:,} Instagram followers")
    if profile.get("shows_count", 0) > 0:
        social_proof_parts.append(f"{profile['shows_count']}+ shows performed")
    if profile.get("experience_years", 0) > 0:
        social_proof_parts.append(f"{profile['experience_years']} years of experience")
    if profile.get("youtube_url"):
        social_proof_parts.append("YouTube presence with performance videos")

    social_proof = ", ".join(social_proof_parts) if social_proof_parts else "growing audience and strong performance track record"

    high_converting_angles = ""
    if analytics_insights and analytics_insights.get("effective_angles"):
        angles = analytics_insights["effective_angles"][:2]
        high_converting_angles = f"\nHigh-converting angles to emphasize: {', '.join(angles)}"

    prompt = f"""You are an expert entertainment booking agent. Write a highly personalized, compelling pitch email from {profile['name']} to {prospect['name']}.

PERFORMER DETAILS:
- Name: {profile['name']}
- Type: {profile.get('entertainer_type', 'performer').title()}
- Genre/Style: {profile.get('genre_style', 'versatile')}
- Location: {profile.get('location', 'US')}
- Experience: {profile.get('experience_years', 0)} years, {profile.get('shows_count', 0)}+ shows
- Social Proof: {social_proof}
- Proposed Rate: ${proposed_rate}/show
- Bio: {profile.get('bio', '')}
- YouTube: {profile.get('youtube_url', 'Available upon request')}
- Instagram: {profile.get('instagram_url', 'Available upon request')}

VENUE/OPPORTUNITY DETAILS:
- Name: {prospect['name']}
- Type: {prospect.get('type', 'venue')}
- Location: {prospect.get('location', 'Unknown')}
- Contact Name: {prospect.get('contact_name', 'Booking Manager')}
- Typical Pay Range: ${prospect.get('typical_pay_min', 0)}-${prospect.get('typical_pay_max', 0)}/show
- Notes: {prospect.get('notes', '')}
{high_converting_angles}

Write a pitch that:
1. Opens with a specific, genuine reference to the venue (their vibe, recent acts they've booked, their reputation)
2. Explains exactly why {profile['name']} is a great fit for THIS specific venue
3. Includes concrete social proof naturally (not as a list)
4. Proposes clear terms (rate, flexibility, availability)
5. Has a clear, low-friction call to action
6. Sounds human, warm, and professional — NOT like a template

Return a JSON object with this structure:
{{
  "subject": "compelling email subject line",
  "body": "full email body with proper paragraphs",
  "key_angle": "the main selling point used in this pitch"
}}

The email should be 150-250 words. Make it feel genuinely tailored to {prospect['name']}, not generic. Return ONLY the JSON."""

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


def generate_pitches_batch(profile: dict, prospects: list, proposed_rate: float, analytics_insights: dict = None) -> list:
    """Generate pitches for multiple prospects."""
    results = []
    for prospect in prospects:
        try:
            pitch = generate_pitch(profile, prospect, proposed_rate, analytics_insights)
            pitch["prospect_id"] = prospect["id"]
            results.append(pitch)
        except Exception as e:
            results.append({
                "prospect_id": prospect["id"],
                "subject": f"Booking Inquiry from {profile['name']}",
                "body": f"Hi {prospect.get('contact_name', 'there')},\n\nI'd love to discuss a potential booking opportunity at {prospect['name']}. I'm {profile['name']}, a {profile.get('entertainer_type', 'performer')} with {profile.get('experience_years', 0)} years of experience. I believe my style would be a great fit for your audience.\n\nI'm available at ${proposed_rate}/show and would love to connect.\n\nBest,\n{profile['name']}",
                "key_angle": "general fit",
                "error": str(e),
            })
    return results
