"""
Agent 1: Market Research & Opportunity Discovery
Researches market rates, finds venues, and identifies opportunities for entertainers.
"""

import json
import os
import anthropic

_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
_simulation_mode = not _api_key or _api_key == "simulation"
client = anthropic.Anthropic(api_key=_api_key or "sk-ant-placeholder") if not _simulation_mode else None

VENUE_TYPES_BY_ENTERTAINER = {
    "comedian": ["Comedy Club", "Corporate Event", "College Venue", "Comedy Festival", "Cruise Ship", "Casino"],
    "rapper": ["Hip-Hop Club", "Music Festival", "College Venue", "Corporate Event", "Bar/Lounge", "Concert Hall"],
    "singer": ["Music Venue", "Wedding", "Corporate Event", "Music Festival", "Restaurant/Bar", "Concert Hall"],
    "musician": ["Music Venue", "Wedding", "Corporate Event", "Music Festival", "Restaurant/Bar", "Concert Hall"],
    "dj": ["Nightclub", "Wedding", "Corporate Event", "Music Festival", "Bar/Lounge", "Private Party"],
    "public speaker": ["Conference", "Corporate Event", "University", "TEDx Event", "Podcast", "Summit"],
    "motivational speaker": ["Conference", "Corporate Event", "University", "Church/Religious Org", "Summit", "Retreat"],
    "magician": ["Corporate Event", "Birthday Party", "Wedding", "Restaurant", "Casino", "Festival"],
    "band": ["Music Venue", "Wedding", "Corporate Event", "Music Festival", "Bar/Restaurant", "Concert Hall"],
    "podcast creator": ["Brand Sponsorship", "Conference Panel", "Podcast Network", "Media Festival", "University", "Online Summit"],
    "content creator": ["Brand Sponsorship", "Conference Panel", "Media Festival", "University", "Online Summit", "Trade Show"],
}

MARKET_RATE_CONTEXT = {
    "comedian": {
        "entry_level": "$50-200/show",
        "mid_level": "$300-1000/show",
        "established": "$1500-5000/show",
        "corporate_premium": "$2000-8000/event",
    },
    "rapper": {
        "entry_level": "$200-800/show",
        "mid_level": "$1000-5000/show",
        "established": "$5000-25000/show",
        "festival_premium": "$3000-15000/set",
    },
    "singer": {
        "entry_level": "$150-500/show",
        "mid_level": "$500-2000/show",
        "established": "$2000-10000/show",
        "wedding_premium": "$1500-5000/event",
    },
    "dj": {
        "entry_level": "$200-500/night",
        "mid_level": "$500-2000/night",
        "established": "$2000-10000/night",
        "festival_premium": "$3000-20000/set",
    },
    "public speaker": {
        "entry_level": "$500-2000/talk",
        "mid_level": "$2000-8000/talk",
        "established": "$8000-25000/talk",
        "keynote_premium": "$15000-75000/keynote",
    },
    "motivational speaker": {
        "entry_level": "$500-2000/talk",
        "mid_level": "$2000-8000/talk",
        "established": "$8000-25000/talk",
        "corporate_premium": "$5000-20000/event",
    },
    "magician": {
        "entry_level": "$150-500/show",
        "mid_level": "$500-2000/show",
        "established": "$2000-8000/show",
        "corporate_premium": "$3000-12000/event",
    },
}


def _determine_experience_tier(experience_years: int, shows_count: int, instagram_followers: int) -> str:
    score = 0
    if experience_years >= 5:
        score += 3
    elif experience_years >= 2:
        score += 2
    else:
        score += 1

    if shows_count >= 100:
        score += 3
    elif shows_count >= 30:
        score += 2
    else:
        score += 1

    if instagram_followers >= 50000:
        score += 3
    elif instagram_followers >= 10000:
        score += 2
    else:
        score += 1

    if score >= 7:
        return "established"
    elif score >= 4:
        return "mid_level"
    else:
        return "entry_level"


def _mock_research(profile: dict, entertainer_type: str, experience_tier: str, rate_context: dict, venue_types: list) -> dict:
    rec_min = int(profile.get("rate_min", 300) * 1.1)
    rec_max = int(profile.get("rate_max", 400) * 1.15)
    avg_rate = int((rec_min + rec_max) / 2)
    location = profile.get("location", "Los Angeles, CA")
    followers = profile.get("instagram_followers", 0)

    mock_venues = [
        {"type": venue_types[0], "examples": ["Club A", "Club B", "Club C"], "typical_pay_min": rec_min - 50, "typical_pay_max": rec_max, "booking_frequency": "Weekly shows available", "fit_score": 9, "notes": f"Best fit for {entertainer_type}s in {location}"},
        {"type": venue_types[1] if len(venue_types) > 1 else "Corporate Event", "examples": ["Corp A", "Corp B", "Corp C"], "typical_pay_min": rec_min * 4, "typical_pay_max": rec_max * 8, "booking_frequency": "Monthly bookings", "fit_score": 7, "notes": "Higher pay, more prep required"},
        {"type": venue_types[2] if len(venue_types) > 2 else "College Venue", "examples": ["University A", "College B", "Campus C"], "typical_pay_min": rec_min, "typical_pay_max": rec_max * 3, "booking_frequency": "High volume — 10-20/year", "fit_score": 8, "notes": "Consistent volume, good for building audience"},
        {"type": venue_types[3] if len(venue_types) > 3 else "Festival", "examples": ["Festival A", "Festival B", "Festival C"], "typical_pay_min": rec_min * 1.5, "typical_pay_max": rec_max * 5, "booking_frequency": "Annual (apply months ahead)", "fit_score": 7, "notes": "Great for brand building"},
        {"type": venue_types[4] if len(venue_types) > 4 else "Private Event", "examples": ["Event A", "Event B", "Event C"], "typical_pay_min": rec_min * 2, "typical_pay_max": rec_max * 4, "booking_frequency": "Seasonal peaks Q4", "fit_score": 6, "notes": "Lucrative but requires referrals"},
    ]

    mock_prospects = []
    for i, vt in enumerate(venue_types[:5]):
        for j in range(6):
            mock_prospects.append({
                "name": f"{location.split(',')[0]} {vt} #{i*6+j+1}",
                "type": vt,
                "location": location,
                "contact_name": f"Booking Manager {i*6+j+1}",
                "contact_email": f"booking{i*6+j+1}@venue{i*6+j+1}.com",
                "typical_pay_min": mock_venues[i]["typical_pay_min"] if i < len(mock_venues) else rec_min,
                "typical_pay_max": mock_venues[i]["typical_pay_max"] if i < len(mock_venues) else rec_max,
                "notes": f"Good fit for {entertainer_type}s — actively booking",
            })

    return {
        "market_insights": {
            "entertainer_type": entertainer_type,
            "experience_tier": experience_tier,
            "market_rates": {
                "entry_level": rate_context.get("entry_level", "$100-300/show"),
                "mid_level": rate_context.get("mid_level", "$300-1000/show"),
                "established": rate_context.get("established", "$1000+/show"),
            },
            "pricing_recommendation": f"Mid-level pricing at ${rec_min}–${rec_max}/show based on your {followers:,} followers and {profile.get('shows_count', 0)} shows",
            "recommended_rate_min": rec_min,
            "recommended_rate_max": rec_max,
            "pricing_rationale": f"Your social proof positions you above entry-level. {entertainer_type.title()}s in {location} with similar credentials typically command ${rec_min}–${rec_max}/show.",
        },
        "venue_opportunities": mock_venues,
        "competitive_analysis": {
            "similar_entertainers_count": 42,
            "average_market_rate": avg_rate,
            "your_current_rate": int(profile.get("rate_max", avg_rate)),
            "positioning": "slightly below market" if profile.get("rate_max", 0) < avg_rate else "at market",
            "recommendation": f"Raising to ${rec_min}–${rec_max} keeps you competitive while reflecting your social proof.",
        },
        "growth_opportunities": [
            {"opportunity": "Add a corporate event tier", "potential_revenue_increase": "3-5x per booking", "effort": "medium"},
            {"opportunity": f"Target college circuit in {location.split(',')[0]}", "potential_revenue_increase": "+8-12 shows/year", "effort": "low"},
            {"opportunity": "Apply to 3 regional festivals", "potential_revenue_increase": "+$2000-6000/year", "effort": "medium"},
            {"opportunity": "Create a highlight reel for pitches", "potential_revenue_increase": "+40% pitch response rate", "effort": "low"},
        ],
        "booking_platforms": [
            {"name": "GigSalad", "best_for": "Corporate & private events", "estimated_monthly_leads": 8},
            {"name": "Gigmit", "best_for": "Clubs & festivals", "estimated_monthly_leads": 12},
            {"name": "BeatGig", "best_for": "College events", "estimated_monthly_leads": 6},
        ],
        "key_insights": [
            f"{venue_types[0]}s average ${rec_min}–${rec_max}/show — you're positioned well",
            f"Corporate events pay 4-8x more — consider adding a corporate tier at ${rec_max*4}+",
            f"Your {followers:,} Instagram followers is above median for {experience_tier} {entertainer_type}s",
            "Video proof in pitches increases response rate by 40-50%",
        ],
        "action_items": [
            f"Raise rate to ${rec_min}–${rec_max} — you're slightly below market",
            f"Target top {venue_types[0]}s first — highest response rate for your type",
            "Create a 2-minute highlight reel for pitch emails",
        ],
        "discovered_prospects": mock_prospects,
        "_simulation": True,
    }


def run_market_research(profile: dict) -> dict:
    entertainer_type = profile.get("entertainer_type", "comedian").lower()
    experience_tier = _determine_experience_tier(
        profile.get("experience_years", 0),
        profile.get("shows_count", 0),
        profile.get("instagram_followers", 0),
    )

    rate_context = MARKET_RATE_CONTEXT.get(entertainer_type, MARKET_RATE_CONTEXT["comedian"])
    venue_types = VENUE_TYPES_BY_ENTERTAINER.get(entertainer_type, VENUE_TYPES_BY_ENTERTAINER["comedian"])

    if _simulation_mode:
        return _mock_research(profile, entertainer_type, experience_tier, rate_context, venue_types)

    prompt = f"""You are an entertainment industry market research expert. Analyze the following entertainer profile and return a comprehensive JSON market research report.

ENTERTAINER PROFILE:
- Name: {profile.get('name')}
- Type: {entertainer_type}
- Genre/Style: {profile.get('genre_style', 'General')}
- Experience: {profile.get('experience_years', 0)} years, {profile.get('shows_count', 0)} shows
- Location: {profile.get('location', 'US')}
- Touring Region: {profile.get('touring_region', 'Regional')}
- Current Rate: ${profile.get('rate_min', 0)}-${profile.get('rate_max', 0)}/show
- Instagram Followers: {profile.get('instagram_followers', 0):,}
- Bio: {profile.get('bio', 'N/A')}

MARKET CONTEXT:
- Experience Tier: {experience_tier}
- Industry Rates: Entry={rate_context.get('entry_level')}, Mid={rate_context.get('mid_level')}, Established={rate_context.get('established')}
- Relevant Venue Types: {', '.join(venue_types)}

Generate a detailed market research report as a JSON object with this EXACT structure:
{{
  "market_insights": {{
    "entertainer_type": "{entertainer_type}",
    "experience_tier": "{experience_tier}",
    "market_rates": {{
      "entry_level": "...",
      "mid_level": "...",
      "established": "..."
    }},
    "pricing_recommendation": "...",
    "recommended_rate_min": <number>,
    "recommended_rate_max": <number>,
    "pricing_rationale": "..."
  }},
  "venue_opportunities": [
    {{
      "type": "...",
      "examples": ["venue1", "venue2", "venue3"],
      "typical_pay_min": <number>,
      "typical_pay_max": <number>,
      "booking_frequency": "...",
      "fit_score": <1-10>,
      "notes": "..."
    }}
  ],
  "competitive_analysis": {{
    "similar_entertainers_count": <number>,
    "average_market_rate": <number>,
    "your_current_rate": <number>,
    "positioning": "below/at/above market",
    "recommendation": "..."
  }},
  "growth_opportunities": [
    {{
      "opportunity": "...",
      "potential_revenue_increase": "...",
      "effort": "low/medium/high"
    }}
  ],
  "booking_platforms": [
    {{
      "name": "...",
      "best_for": "...",
      "estimated_monthly_leads": <number>
    }}
  ],
  "key_insights": ["insight1", "insight2", "insight3"],
  "action_items": ["action1", "action2", "action3"]
}}

Be specific, realistic, and tailored to the {entertainer_type}'s market in {profile.get('location', 'the US')}. Include 5-7 venue opportunity types and 3-4 growth opportunities. Return ONLY the JSON object, no other text."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    data = json.loads(raw)

    discovered_prospects = _generate_prospect_list(profile, data, entertainer_type)
    data["discovered_prospects"] = discovered_prospects

    return data


def _generate_prospect_list(profile: dict, research_data: dict, entertainer_type: str) -> list:
    location = profile.get("location", "Los Angeles, CA")
    venue_opps = research_data.get("venue_opportunities", [])

    prompt = f"""Generate a list of 30 real or realistic {entertainer_type} booking prospects in and around {location}.

Venue types to include: {', '.join([v.get('type', '') for v in venue_opps[:5]])}

Return a JSON array of prospect objects with this structure:
[
  {{
    "name": "Venue/Organization Name",
    "type": "venue type",
    "location": "City, State",
    "contact_name": "Booking Manager Name",
    "contact_email": "booking@venue.com",
    "typical_pay_min": <number>,
    "typical_pay_max": <number>,
    "notes": "Brief note about why this is a good fit"
  }}
]

Make the names realistic and varied. Include a mix of venue types. For {entertainer_type}s in {location}, be specific about real venue categories that exist there. Return ONLY the JSON array."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    prospects = json.loads(raw)
    return prospects
