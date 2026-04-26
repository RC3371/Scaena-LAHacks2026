import json
import os
import re
from urllib.parse import urlparse

import httpx


GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
GOOGLE_SEARCH_URL = "https://customsearch.googleapis.com/customsearch/v1"
EVENTBRITE_SEARCH_URL = "https://www.eventbriteapi.com/v3/events/search/"


def live_sources_configured() -> bool:
    google_key, google_cx = _google_config()
    return bool(
        _gemini_key()
        or (google_key and google_cx)
        or os.getenv("EVENTBRITE_API_TOKEN")
        or os.getenv("EVENTBRITE_API_KEY")
    )


def discover_live_venues(entertainer: dict, user_instruction: str = "") -> dict | None:
    location = entertainer.get("location") or "Los Angeles, CA"
    etype = entertainer.get("type") or "performer"
    genre = entertainer.get("genre") or etype
    highlights = entertainer.get("highlights") or ""
    rate = float(entertainer.get("current_rate") or 350)
    query_seed = user_instruction or highlights or f"{genre} {etype} booking opportunities"

    results: list[dict] = []
    gemini_insights = ""
    gemini_data = _gemini_grounded_results(query_seed, location, etype, genre, rate)
    if gemini_data:
        results.extend(gemini_data.get("venues", []))
        gemini_insights = gemini_data.get("market_insights", "")
    results.extend(_eventbrite_events(query_seed, location, etype))
    results.extend(_google_general_results(query_seed, location, etype, genre))
    results.extend(_google_peerspace_results(query_seed, location, etype, genre))
    results.extend(_google_social_results(query_seed, location, etype, genre))

    venues = _prepare_opportunities(results, etype, genre, location, rate, query_seed)
    venues = _dedupe(venues)[: int(os.getenv("MARKET_RESEARCH_MAX_RESULTS", "12"))]
    if not venues:
        return None

    return {
        "market_rate_low": max(0, round(rate * 0.75)),
        "market_rate_high": round(rate * 1.6),
        "recommended_rate": rate,
        "pricing_trend": "stable",
        "venues": venues,
        "market_insights": gemini_insights or (
            f"Live discovery searched Google-indexed venue pages, campus/event pages, Eventbrite listings, "
            f"Peerspace spaces, and public social pages around {location}. Each match is prioritized for "
            f"booking path, audience fit, and next outreach step; verify source links before real outreach."
        ),
    }


def curated_opportunity_fallback(entertainer: dict, user_instruction: str = "") -> dict:
    location = entertainer.get("location") or "Los Angeles, CA"
    etype = entertainer.get("type") or "performer"
    genre = entertainer.get("genre") or etype
    rate = float(entertainer.get("current_rate") or 350)
    name = entertainer.get("name") or "the artist"
    query_seed = user_instruction or entertainer.get("highlights") or ""
    test_email = os.getenv("GMAIL_TEST_RECIPIENT") or None

    if any(term in f"{etype} {genre}".lower() for term in ["rapper", "hip-hop", "hip hop", "music", "singer", "band"]):
        raw = [
            {
                "name": "UCLA Student Union Event Services",
                "venue_type": "College",
                "typical_pay": f"Verify student budget; target around ${rate:.0f}",
                "fit_score": 0.92,
                "contact_name": "Booking Team",
                "contact_email": test_email,
                "source_url": "https://www.asucla.ucla.edu/student-union-event-services",
                "why_fits": f"Campus event services are a strong buyer path for {name}: student programming, high foot traffic, and a clear events office.",
                "specific_examples": ["campus programming", "student event office", "buyer path: reservations/events"],
            },
            {
                "name": "KOXY Radio Station, Occidental College",
                "venue_type": "College",
                "typical_pay": f"Verify student budget; target around ${rate:.0f}",
                "fit_score": 0.9,
                "contact_name": "Booking Team",
                "contact_email": test_email,
                "source_url": "https://www.oxy.edu/student-life/leadership-involvement/koxy-radio-station",
                "why_fits": "College radio teams often touch student concerts and on-campus music culture, making them useful warm entry points.",
                "specific_examples": ["college radio", "campus concerts", "buyer path: student music programming"],
            },
            {
                "name": "Catch One",
                "venue_type": "Music Venue",
                "typical_pay": f"Verify door deal or support slot; target around ${rate:.0f}",
                "fit_score": 0.88,
                "contact_name": "Booking Team",
                "contact_email": test_email,
                "source_url": "https://catch.one/",
                "why_fits": "A real LA room with hip-hop and nightlife crossover potential, useful for support slots and themed bills.",
                "specific_examples": ["LA music venue", "hip-hop/nightlife crossover", "buyer path: booking desk"],
            },
            {
                "name": "The Virgil",
                "venue_type": "Bar | Music Venue",
                "typical_pay": f"Verify bar/showcase budget; target around ${rate:.0f}",
                "fit_score": 0.84,
                "contact_name": "Booking Team",
                "contact_email": test_email,
                "source_url": "https://thevirgil.com/",
                "why_fits": "A smaller LA bar/music room is a realistic paid showcase target for building repeat local audience.",
                "specific_examples": ["bar/music venue", "showcase slot", "buyer path: venue booking contact"],
            },
            {
                "name": "LACC Herb Alpert Music Center",
                "venue_type": "College | Event Series",
                "typical_pay": f"Verify department/event budget; target around ${rate:.0f}",
                "fit_score": 0.78,
                "contact_name": "Booking Team",
                "contact_email": test_email,
                "source_url": "https://www.lacc.edu/academic/departments/music/music-events",
                "why_fits": "College music departments and event series can be useful exposure plays when framed as student-facing programming.",
                "specific_examples": ["college music events", "guest artist lane", "buyer path: department events contact"],
            },
        ]
    else:
        raw = [
            {
                "name": f"{location} Campus Events Office",
                "venue_type": "College",
                "typical_pay": f"Verify budget; target around ${rate:.0f}",
                "fit_score": 0.84,
                "contact_name": "Booking Team",
                "contact_email": test_email,
                "source_url": "",
                "why_fits": f"Campus programming can book emerging {etype}s for high-exposure events with clear student audiences.",
                "specific_examples": ["student activities", "campus programming", "buyer path: events office"],
            },
            {
                "name": f"{location} Event Producer Lead",
                "venue_type": "Event Producer",
                "typical_pay": f"Verify budget; target around ${rate:.0f}",
                "fit_score": 0.76,
                "contact_name": "Booking Team",
                "contact_email": test_email,
                "source_url": "",
                "why_fits": "Independent producers can place talent across venues, private events, and recurring showcases.",
                "specific_examples": ["event producer", "showcase calendar", "buyer path: organizer"],
            },
        ]

    venues = _prepare_opportunities(raw, etype, genre, location, rate, query_seed)
    return {
        "market_rate_low": max(0, round(rate * 0.75)),
        "market_rate_high": round(rate * 1.6),
        "recommended_rate": rate,
        "pricing_trend": "stable",
        "venues": venues,
        "market_insights": (
            "Live provider quota was unavailable, so Scaena generated an agent-curated fallback list from known buyer lanes. "
            "Use these as demo-safe opportunities and verify source pages before real outreach."
        ),
    }


def _gemini_key() -> str | None:
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


def _gemini_grounded_results(query_seed: str, location: str, etype: str, genre: str, rate: float) -> dict | None:
    api_key = _gemini_key()
    if not api_key:
        return None

    model = os.getenv("GEMINI_GROUNDING_MODEL", "gemini-2.5-flash")
    prompts = [
        f"""
You are a senior booking agent replacing the manual work of a celebrity talent agent.
Use Google Search grounding to find real-world booking opportunities for this entertainer.

Artist type: {etype}
Genre: {genre}
Location: {location}
Target search brief: {query_seed}
Target rate: about ${rate:.0f} per booking

Find 5 strong organizations, venues, event series, campuses, festivals, bars, music venues, or event spaces that could realistically book this act.
A useful lead has a plausible buyer, a real booking path, the right audience, and a reason to contact them now. Avoid generic listicles unless they point to a specific venue.
Prioritize real source pages and public booking/event pages. Use short canonical source URLs, not Google or Vertex grounding redirect URLs. Do not invent email addresses or names. If a direct booking contact is not visible, use null for contact_email and "Booking Team" for contact_name. Fit scores must be numbers from 0.0 to 1.0.

Return only valid JSON with this exact shape:
{{
  "market_insights": "2 concise sentences about the best booking lanes and outreach cautions.",
  "venues": [
    {{
      "name": "real organization or venue name",
      "venue_type": "College | Festival | Music Venue | Bar | Event Space | Social Lead | Other",
      "typical_pay": "short estimate or Verify from source",
      "fit_score": 0.86,
      "contact_name": "visible contact name or Booking Team",
      "contact_email": null,
      "source_url": "best source URL",
      "contact_approach": "specific next outreach step a booking agent would take",
      "why_fits": "one human-readable reason tied to the artist, audience, and source",
      "specific_examples": ["source clue", "event/program clue", "buyer or booking lane"]
    }}
  ]
}}
""".strip(),
        f"""
Use Google Search grounding and return JSON only. Think like a booking agent, not a directory scraper.

Find exactly 5 specific, real booking targets near {location} for a {genre} {etype} with a target rate near ${rate:.0f}.
The user specifically wants: {query_seed}

Prioritize these live-source lanes:
1. college campus programming boards and student event offices
2. LA music venues and bars with live music or hip-hop programming
3. student festivals, campus concerts, and showcase/event pages
4. Peerspace or public social/event pages only when they point to a usable venue or organizer

Do not invent emails. Use null for contact_email unless the source visibly provides one.
Every venue must include a short canonical source_url, not a Google or Vertex grounding redirect URL.
Avoid weak leads like broad city guides, unrelated academic pages, personal social profiles, or pages without a plausible buyer path.

Return this JSON shape exactly:
{{
  "market_insights": "2 concise sentences about strongest lanes and any outreach caution.",
  "venues": [
    {{
      "name": "real venue, organization, board, or event series",
      "venue_type": "College | Festival | Music Venue | Bar | Event Space | Social Lead | Other",
      "typical_pay": "Verify from source",
      "fit_score": 0.86,
      "contact_name": "Booking Team",
      "contact_email": null,
      "source_url": "https://source-page.example",
      "contact_approach": "specific next outreach step a booking agent would take",
      "why_fits": "one reason this target fits the artist, audience, and source",
      "specific_examples": ["source clue", "program or event clue", "buyer or booking lane"]
    }}
  ]
}}
""".strip(),
    ]

    for prompt in prompts:
        payload = _gemini_grounded_payload(api_key, model, prompt)
        if not payload:
            continue
        text = _gemini_text(payload)
        parsed = _parse_json_object(text)
        if not parsed:
            continue
        venues = _gemini_venues_from_payload(parsed, payload, etype, genre)
        if venues:
            return {
                "market_insights": _clean_text(str(parsed.get("market_insights") or "")),
                "venues": venues,
            }

    return None


def _gemini_grounded_payload(api_key: str, model: str, prompt: str) -> dict | None:
    try:
        resp = httpx.post(
            GEMINI_API_URL.format(model=model),
            headers={
                "x-goog-api-key": api_key,
                "Content-Type": "application/json",
            },
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "tools": [{"google_search": {}}],
                "generationConfig": {
                    "temperature": 0.15,
                    "maxOutputTokens": 6000,
                },
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def _gemini_venues_from_payload(parsed: dict, payload: dict, etype: str, genre: str) -> list[dict]:
    sources = _gemini_sources(payload)
    raw_venues = parsed.get("venues", []) if isinstance(parsed, dict) else []
    venues = []
    for index, raw in enumerate(raw_venues):
        if not isinstance(raw, dict):
            continue
        name = _clean_text(str(raw.get("name") or ""))
        if not name:
            continue

        source = sources[index] if index < len(sources) else {}
        link = _clean_text(str(raw.get("source_url") or source.get("uri") or ""))
        venue_type = _clean_text(str(raw.get("venue_type") or _venue_type_for(etype, genre)))
        examples = _as_text_list(raw.get("specific_examples"))
        if source.get("title"):
            examples.append(source["title"])

        venues.append(
            {
                "name": name[:90],
                "venue_type": venue_type or _venue_type_for(etype, genre),
                "typical_pay": _clean_text(str(raw.get("typical_pay") or "Verify from source")),
                "fit_score": _fit_score(raw.get("fit_score"), 0.86),
                "contact_name": _clean_text(str(raw.get("contact_name") or "Booking Team")) or "Booking Team",
                "contact_email": _clean_email(raw.get("contact_email")) or os.getenv("GMAIL_TEST_RECIPIENT") or None,
                "source_url": link,
                "contact_approach": _clean_text(str(raw.get("contact_approach") or "Open source page and verify the booking contact.")),
                "why_fits": _clean_text(str(raw.get("why_fits") or f"Found through Gemini Search grounding for {genre} {etype} bookings.")),
                "specific_examples": examples[:4] or ["Gemini Search grounding"],
            }
        )

    return venues


def _gemini_text(payload: dict) -> str:
    candidates = payload.get("candidates") or []
    if not candidates:
        return ""
    parts = ((candidates[0].get("content") or {}).get("parts") or [])
    return "\n".join(str(part.get("text") or "") for part in parts)


def _gemini_sources(payload: dict) -> list[dict]:
    candidates = payload.get("candidates") or []
    if not candidates:
        return []
    metadata = candidates[0].get("groundingMetadata") or {}
    chunks = metadata.get("groundingChunks") or []
    sources = []
    for chunk in chunks:
        web = chunk.get("web") or {}
        uri = web.get("uri")
        if uri:
            sources.append({"uri": uri, "title": _clean_text(web.get("title") or _domain(uri))})
    return sources


def _parse_json_object(text: str) -> dict | None:
    if not text:
        return None
    cleaned = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", cleaned, re.DOTALL | re.IGNORECASE)
    if fenced:
        cleaned = fenced.group(1).strip()
    if not cleaned.startswith("{"):
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(0)
    try:
        parsed = json.loads(cleaned)
    except Exception:
        return _salvage_venue_json(cleaned)
    return parsed if isinstance(parsed, dict) else None


def _salvage_venue_json(text: str) -> dict | None:
    """Recover useful venue objects from a grounded response that was cut off mid-JSON."""
    insight = ""
    insight_match = re.search(r'"market_insights"\s*:\s*"((?:\\.|[^"\\])*)"', text, flags=re.DOTALL)
    if insight_match:
        try:
            insight = json.loads(f'"{insight_match.group(1)}"')
        except Exception:
            insight = _clean_text(insight_match.group(1))

    venues_start = re.search(r'"venues"\s*:\s*\[', text)
    if not venues_start:
        return None

    venues_text = text[venues_start.end():]
    objects: list[dict] = []
    depth = 0
    start = None
    in_string = False
    escaped = False
    for idx, char in enumerate(venues_text):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
            continue
        if char == "{":
            if depth == 0:
                start = idx
            depth += 1
            continue
        if char == "}":
            if depth:
                depth -= 1
            if depth == 0 and start is not None:
                raw_obj = venues_text[start: idx + 1]
                try:
                    parsed = json.loads(raw_obj)
                except Exception:
                    parsed = None
                if isinstance(parsed, dict):
                    objects.append(parsed)
                start = None

    return {"market_insights": insight, "venues": objects} if objects else None


def _google_config() -> tuple[str | None, str | None]:
    api_key = (
        os.getenv("GOOGLE_SEARCH_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or os.getenv("GEMINI_API_KEY")
    )
    cx = (
        os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        or os.getenv("GOOGLE_CSE_ID")
        or os.getenv("GOOGLE_CUSTOM_SEARCH_CX")
    )
    return api_key, cx


def _google_search(query: str, source: str, venue_type: str, num: int = 5) -> list[dict]:
    api_key, cx = _google_config()
    if not api_key or not cx:
        return []

    try:
        resp = httpx.get(
            GOOGLE_SEARCH_URL,
            params={
                "key": api_key,
                "cx": cx,
                "q": query,
                "num": max(1, min(num, 10)),
                "safe": "active",
            },
            timeout=12,
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])
    except Exception:
        return []

    venues = []
    for item in items:
        title = _clean_title(item.get("title") or "Venue lead")
        link = item.get("link") or ""
        snippet = _clean_text(item.get("snippet") or "")
        if not link:
            continue
        venues.append(
            {
                "name": title,
                "venue_type": venue_type,
                "typical_pay": "Verify from source",
                "fit_score": _score_for_source(source),
                "contact_name": "Booking Team",
                "contact_email": os.getenv("GMAIL_TEST_RECIPIENT") or None,
                "source_url": link,
                "contact_approach": _contact_approach(source),
                "why_fits": snippet or f"Found via {source} live search for this artist profile.",
                "specific_examples": [source, _domain(link)],
            }
        )
    return venues


def _google_general_results(query_seed: str, location: str, etype: str, genre: str) -> list[dict]:
    query = (
        f'{query_seed} "{location}" ("booking" OR "talent buyer" OR "event services" OR "student programming" '
        f'OR "live music" OR "campus events" OR festival OR bar)'
    )
    return _google_search(query, "Google", _venue_type_for(etype, genre), num=6)


def _google_peerspace_results(query_seed: str, location: str, etype: str, genre: str) -> list[dict]:
    query = f'site:peerspace.com "{location}" "{genre}" event space performance venue {query_seed}'
    return _google_search(query, "Peerspace", "Event Space", num=4)


def _google_social_results(query_seed: str, location: str, etype: str, genre: str) -> list[dict]:
    query = (
        f'("{location}" "{genre}" "{etype}" booking OR showcase OR "live music") '
        f'(site:instagram.com OR site:tiktok.com OR site:facebook.com/events)'
    )
    return _google_search(query, "Social", "Social Lead", num=5)


def _eventbrite_events(query_seed: str, location: str, etype: str) -> list[dict]:
    token = os.getenv("EVENTBRITE_API_TOKEN") or os.getenv("EVENTBRITE_API_KEY")
    if not token:
        return []

    try:
        resp = httpx.get(
            EVENTBRITE_SEARCH_URL,
            headers={"Authorization": f"Bearer {token}"},
            params={
                "q": query_seed,
                "location.address": location,
                "expand": "venue,organizer",
                "sort_by": "date",
                "page_size": 10,
            },
            timeout=12,
        )
        resp.raise_for_status()
        events = resp.json().get("events", [])
    except Exception:
        return []

    venues = []
    for event in events:
        name = _clean_text((event.get("venue") or {}).get("name") or (event.get("name") or {}).get("text") or "Eventbrite lead")
        event_name = _clean_text((event.get("name") or {}).get("text") or name)
        organizer = _clean_text((event.get("organizer") or {}).get("name") or "Organizer")
        summary = _clean_text(event.get("summary") or (event.get("description") or {}).get("text") or "")
        link = event.get("url") or ""
        venues.append(
            {
                "name": name,
                "venue_type": "Eventbrite Event",
                "typical_pay": "Verify with organizer",
                "fit_score": 0.82,
                "contact_name": organizer,
                "contact_email": os.getenv("GMAIL_TEST_RECIPIENT") or None,
                "source_url": link,
                "contact_approach": "Open Eventbrite event page; identify organizer and booking contact.",
                "why_fits": summary or f"Eventbrite listing related to {etype} opportunities: {event_name}.",
                "specific_examples": ["Eventbrite", event_name],
            }
        )
    return venues


def _dedupe(venues: list[dict]) -> list[dict]:
    seen: set[str] = set()
    unique: list[dict] = []
    for venue in venues:
        key = _normalize_key(venue.get("source_url") or venue.get("name") or "")
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(venue)
    unique.sort(key=lambda v: v.get("fit_score") or 0, reverse=True)
    return unique


def _unique_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = _clean_text(str(value))
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(cleaned)
    return result


def _prepare_opportunities(
    venues: list[dict],
    etype: str,
    genre: str,
    location: str,
    rate: float,
    query_seed: str,
) -> list[dict]:
    prepared = []
    for venue in venues:
        if not isinstance(venue, dict):
            continue
        name = _clean_title(str(venue.get("name") or ""))
        if not _useful_name(name):
            continue

        source_url = _best_source_url(venue)
        source_domain = _domain(source_url) if source_url else ""
        venue_type = _clean_text(str(venue.get("venue_type") or _venue_type_for(etype, genre)))
        score = _fit_score(venue.get("fit_score"), _score_for_venue_type(venue_type, source_domain))
        score = _boost_score(score, venue_type, source_url, venue)
        priority = _priority_for(score)
        lane = _lane_for(venue_type, source_domain, venue)
        next_step = _agent_next_step(venue, venue_type, source_domain)
        examples = _as_text_list(venue.get("specific_examples"))
        if lane:
            examples.append(f"Lane: {lane}")
        if priority:
            examples.append(f"Priority: {priority}")
        if next_step:
            examples.append(f"Next step: {next_step}")
        if source_domain:
            examples.append(f"Source: {source_domain}")

        why = _clean_text(str(venue.get("why_fits") or ""))
        if not why:
            why = (
                f"This is a {priority.lower()} opportunity because it matches the artist's {genre or etype} audience, "
                f"has a plausible buyer path, and sits near the {location} target market."
            )
        elif "opportunity" not in why.lower():
            why = f"Opportunity: {lane}. {why}"

        prepared.append({
            **venue,
            "name": name,
            "venue_type": venue_type,
            "typical_pay": _clean_text(str(venue.get("typical_pay") or f"Verify budget; target around ${rate:.0f}")),
            "fit_score": score,
            "contact_name": _clean_text(str(venue.get("contact_name") or "Booking Team")) or "Booking Team",
            "contact_email": _clean_email(venue.get("contact_email")) or os.getenv("GMAIL_TEST_RECIPIENT") or None,
            "source_url": source_url,
            "contact_approach": next_step,
            "why_fits": why[:700],
            "specific_examples": _unique_preserve_order(examples)[:6],
        })
    return prepared


def _useful_name(name: str) -> bool:
    if not name:
        return False
    lowered = name.lower()
    weak = {
        "venue lead",
        "events",
        "music",
        "home",
        "calendar",
        "contact",
        "event calendar",
    }
    return lowered not in weak and len(lowered) > 2


def _best_source_url(venue: dict) -> str:
    candidates = [str(venue.get("source_url") or "").strip()]
    for item in _as_text_list(venue.get("specific_examples")):
        if item.startswith("http"):
            candidates.append(item)
    for link in candidates:
        if _is_useful_source_url(link):
            return link
    return ""


def _is_useful_source_url(url: str) -> bool:
    if not url or not url.startswith(("http://", "https://")):
        return False
    domain = _domain(url).lower()
    bad_domains = [
        "google.com",
        "vertexaisearch.cloud.google.com",
        "accounts.google.com",
        "search.google.com",
    ]
    return not any(domain == bad or domain.endswith(f".{bad}") for bad in bad_domains)


def _score_for_venue_type(venue_type: str, source_domain: str) -> float:
    text = f"{venue_type} {source_domain}".lower()
    if any(term in text for term in ["college", "university", ".edu", "campus", "student"]):
        return 0.9
    if any(term in text for term in ["festival", "eventbrite", "showcase"]):
        return 0.86
    if any(term in text for term in ["music venue", "bar", "nightclub", "live music"]):
        return 0.84
    if any(term in text for term in ["peerspace", "event space"]):
        return 0.76
    if "social" in text:
        return 0.72
    return 0.7


def _boost_score(score: float, venue_type: str, source_url: str, venue: dict) -> float:
    text = " ".join([
        venue_type,
        source_url,
        str(venue.get("contact_approach") or ""),
        str(venue.get("why_fits") or ""),
        " ".join(_as_text_list(venue.get("specific_examples"))),
    ]).lower()
    if any(term in text for term in ["booking", "event services", "programming", "student", "talent buyer", "concert"]):
        score += 0.05
    if _clean_email(venue.get("contact_email")):
        score += 0.04
    if source_url:
        score += 0.03
    if any(term in text for term in ["listicle", "things to do", "blog", "guide"]):
        score -= 0.08
    return max(0.0, min(score, 0.98))


def _priority_for(score: float) -> str:
    if score >= 0.9:
        return "Hot"
    if score >= 0.78:
        return "Warm"
    return "Verify"


def _lane_for(venue_type: str, source_domain: str, venue: dict) -> str:
    text = " ".join([
        venue_type,
        source_domain,
        str(venue.get("name") or ""),
        str(venue.get("why_fits") or ""),
        " ".join(_as_text_list(venue.get("specific_examples"))),
    ]).lower()
    if any(term in text for term in ["college", "university", ".edu", "campus", "student"]):
        return "campus programming"
    if any(term in text for term in ["festival", "eventbrite", "showcase"]):
        return "festival/showcase"
    if any(term in text for term in ["bar", "nightclub"]):
        return "bar/nightlife"
    if any(term in text for term in ["music venue", "concert", "live music"]):
        return "music venue"
    if "peerspace" in text or "event space" in text:
        return "private event space"
    if any(term in text for term in ["instagram", "tiktok", "facebook"]):
        return "public social lead"
    return "venue lead"


def _agent_next_step(venue: dict, venue_type: str, source_domain: str) -> str:
    approach = _clean_text(str(venue.get("contact_approach") or ""))
    if approach and "open source page" not in approach.lower():
        return approach[:260]
    text = f"{venue_type} {source_domain}".lower()
    if any(term in text for term in ["college", "university", ".edu", "campus", "student"]):
        return "Find the student programming or event services contact, then pitch a student-friendly set with rate, reel, and flexible dates."
    if "eventbrite" in text or "festival" in text:
        return "Identify the organizer or submission page, then send a short festival/showcase pitch with EPK and set-length options."
    if "peerspace" in text:
        return "Use the host inquiry flow only if the space supports live music, then ask whether they book talent or refer event producers."
    if any(term in text for term in ["instagram", "tiktok", "facebook"]):
        return "Use the public business contact link first; use DM only as a follow-up when the page clearly represents the venue."
    if any(term in text for term in ["bar", "nightclub", "music"]):
        return "Email the talent buyer or booking desk with a concise local draw, target rate, reel, and two possible show windows."
    return "Verify the buyer path on the source page, then send a concise booking pitch with rate, reel, and availability."


def _normalize_key(value: str) -> str:
    parsed = urlparse(value)
    if parsed.netloc:
        return f"{parsed.netloc.lower()}{parsed.path}".rstrip("/")
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _clean_title(title: str) -> str:
    title = _clean_text(title)
    for sep in [" | ", " - ", " \u2013 "]:
        if sep in title:
            title = title.split(sep)[0].strip()
    return title[:90] or "Venue lead"


def _clean_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _clean_email(value) -> str | None:
    if not value:
        return None
    email = _clean_text(str(value))
    if email.lower() in {"null", "none", "n/a", "na", "unknown"}:
        return None
    return email if "@" in email else None


def _as_text_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [_clean_text(str(item)) for item in value if _clean_text(str(item))]
    text = _clean_text(str(value))
    return [text] if text else []


def _fit_score(value, fallback: float) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return fallback
    if score > 1:
        score = score / 100
    return max(0.0, min(score, 1.0))


def _domain(url: str) -> str:
    return urlparse(url).netloc.replace("www.", "")


def _score_for_source(source: str) -> float:
    return {
        "Google": 0.84,
        "Peerspace": 0.78,
        "Social": 0.74,
    }.get(source, 0.72)


def _contact_approach(source: str) -> str:
    if source == "Peerspace":
        return "Use Peerspace host inquiry workflow or source page contact details."
    if source == "Social":
        return "Use public business contact link or approved DM workflow; avoid personal accounts."
    return "Open source page and use listed booking, talent buyer, or events contact."


def _venue_type_for(etype: str, genre: str) -> str:
    text = f"{etype} {genre}".lower()
    if "speaker" in text:
        return "Conference / University"
    if "dj" in text:
        return "Nightlife / Event"
    if any(term in text for term in ["rapper", "music", "singer", "band"]):
        return "Music Venue"
    if "comedian" in text:
        return "Comedy / Event Venue"
    return "Venue Lead"
