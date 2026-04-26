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

    venues = _dedupe(results)[: int(os.getenv("MARKET_RESEARCH_MAX_RESULTS", "12"))]
    if not venues:
        return None

    return {
        "market_rate_low": max(0, round(rate * 0.75)),
        "market_rate_high": round(rate * 1.6),
        "recommended_rate": rate,
        "pricing_trend": "stable",
        "venues": venues,
        "market_insights": gemini_insights or (
            f"Live discovery searched Google-indexed venue pages, Eventbrite listings, Peerspace spaces, "
            f"and public social/event pages around {location}. Review source links before outreach; "
            f"social leads should use public business contact links or approved DM workflows only."
        ),
    }


def _gemini_key() -> str | None:
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


def _gemini_grounded_results(query_seed: str, location: str, etype: str, genre: str, rate: float) -> dict | None:
    api_key = _gemini_key()
    if not api_key:
        return None

    model = os.getenv("GEMINI_GROUNDING_MODEL", "gemini-2.5-flash")
    prompt = f"""
Use Google Search grounding to find real-world booking opportunities for this entertainer.

Artist type: {etype}
Genre: {genre}
Location: {location}
Target search brief: {query_seed}
Target rate: about ${rate:.0f} per booking

Find organizations, venues, event series, campuses, festivals, bars, music venues, or event spaces that could realistically book this act.
Prioritize real source pages and public booking/event pages. Do not invent email addresses or names. If a direct booking contact is not visible, use null for contact_email and "Booking Team" for contact_name. Fit scores must be numbers from 0.0 to 1.0.

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
      "contact_approach": "specific next outreach step",
      "why_fits": "one human-readable reason tied to the artist and source",
      "specific_examples": ["source clue", "event/program clue"]
    }}
  ]
}}
""".strip()

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
                    "temperature": 0.2,
                    "maxOutputTokens": 3500,
                },
            },
            timeout=30,
        )
        resp.raise_for_status()
        payload = resp.json()
    except Exception:
        return None

    text = _gemini_text(payload)
    parsed = _parse_json_object(text)
    if not parsed:
        return None

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

    if not venues:
        return None

    return {
        "market_insights": _clean_text(str(parsed.get("market_insights") or "")) if isinstance(parsed, dict) else "",
        "venues": venues,
    }


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
        return None
    return parsed if isinstance(parsed, dict) else None


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
        f'{query_seed} "{location}" booking talent buyer OR "live music" OR "student events" '
        f'OR festival OR bar'
    )
    return _google_search(query, "Google", _venue_type_for(etype, genre), num=6)


def _google_peerspace_results(query_seed: str, location: str, etype: str, genre: str) -> list[dict]:
    query = f'site:peerspace.com "{location}" "{genre}" event space performance venue {query_seed}'
    return _google_search(query, "Peerspace", "Event Space", num=4)


def _google_social_results(query_seed: str, location: str, etype: str, genre: str) -> list[dict]:
    query = (
        f'("{location}" "{genre}" "{etype}" booking) '
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
