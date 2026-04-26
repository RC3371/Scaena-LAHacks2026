import base64
import hashlib
import hmac
import html
import json
import os
import re
import secrets
import time
from datetime import datetime, timedelta
from email.utils import parseaddr
from email.message import EmailMessage
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request as FastAPIRequest
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from backend import models
from backend.database import get_db
from backend.services.conversation_context import (
    conversation_messages_payload as shared_conversation_messages_payload,
    prior_venue_context,
)
from backend.services.booking_pipeline import ensure_booking_for_pitch
from backend.services.booking_logistics import apply_auto_logistics_to_booking
from backend.services.mongo_store import mirror_agent_event, mirror_pitch_sent
from backend.services.pitch_generation import (
    build_conversation_memory,
    conversation_completion_status,
    ensure_team_signoff,
    generate_reply_draft,
    greeting_for,
    remove_long_dashes,
    reply_has_specific_date,
)
from backend.websocket_manager import manager

router = APIRouter(prefix="/gmail", tags=["gmail"])

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "openid",
    "email",
]

_oauth_states: dict[str, dict[str, str]] = {}


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _frontend_url() -> str:
    return os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")


def _redirect_uri() -> str:
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
    return os.getenv("GOOGLE_REDIRECT_URI", f"{backend_url}/gmail/oauth2callback")


def _client_config() -> dict:
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise HTTPException(
            status_code=503,
            detail="Gmail OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.",
        )
    return {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [_redirect_uri()],
        }
    }


def _safe_return_to(return_to: Optional[str]) -> str:
    if not return_to or not return_to.startswith("/") or return_to.startswith("//"):
        return "/onboarding?gmail=connected"
    return return_to


def _state_secret() -> bytes:
    secret = os.getenv("GOOGLE_CLIENT_SECRET") or os.getenv("ASI1_API_KEY") or "scaena-local-oauth-state"
    return secret.encode("utf-8")


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + ("=" * (-len(value) % 4)))


def _sign_oauth_state(payload: dict) -> str:
    packed = _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(_state_secret(), packed.encode("utf-8"), hashlib.sha256).digest()
    return f"{packed}.{_b64encode(signature)}"


def _verify_oauth_state(state: str) -> Optional[dict]:
    if not state or "." not in state:
        return None
    packed, supplied_sig = state.rsplit(".", 1)
    expected_sig = _b64encode(hmac.new(_state_secret(), packed.encode("utf-8"), hashlib.sha256).digest())
    if not hmac.compare_digest(supplied_sig, expected_sig):
        return None
    try:
        payload = json.loads(_b64decode(packed).decode("utf-8"))
    except Exception:
        return None
    if int(payload.get("exp", 0)) < int(time.time()):
        return None
    return payload if isinstance(payload, dict) else None


def _account_scopes(account: Optional[models.GmailAccount]) -> list[str]:
    if not account:
        return []
    try:
        scopes = json.loads(account.scopes or "[]")
    except Exception:
        scopes = []
    return [str(scope) for scope in scopes]


def _has_read_scope(account: Optional[models.GmailAccount]) -> bool:
    scopes = _account_scopes(account)
    return any(scope.endswith("/auth/gmail.readonly") or scope.endswith("/auth/gmail.modify") for scope in scopes)


def _build_flow(state: Optional[str] = None):
    try:
        from google_auth_oauthlib.flow import Flow
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail="Gmail dependencies are missing. Run: pip install -r requirements.txt",
        ) from exc

    redirect_uri = _redirect_uri()
    if redirect_uri.startswith("http://"):
        os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

    flow = Flow.from_client_config(
        _client_config(),
        scopes=SCOPES,
        state=state,
        redirect_uri=redirect_uri,
        autogenerate_code_verifier=False,
    )
    return flow


def _exchange_oauth_code(code: str) -> dict:
    try:
        resp = httpx.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "redirect_uri": _redirect_uri(),
                "grant_type": "authorization_code",
            },
            timeout=15,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Could not reach Google OAuth token endpoint. Check network and retry Gmail connection.",
        ) from exc

    try:
        payload = resp.json()
    except Exception:
        payload = {}

    if resp.status_code != 200:
        google_error = payload.get("error_description") or payload.get("error") or "Google rejected the OAuth code."
        raise HTTPException(
            status_code=400,
            detail=f"Gmail OAuth token exchange failed: {google_error}",
        )
    if not payload.get("access_token"):
        raise HTTPException(status_code=400, detail="Gmail OAuth token exchange failed: no access token returned.")
    return payload


def _gmail_http_error_detail(exc) -> str:
    status = getattr(getattr(exc, "resp", None), "status", None)
    message = ""
    reason = ""
    try:
        payload = json.loads((getattr(exc, "content", b"") or b"{}").decode("utf-8"))
        error = payload.get("error") or {}
        message = error.get("message") or ""
        details = error.get("errors") or error.get("details") or []
        if details and isinstance(details[0], dict):
            reason = details[0].get("reason") or ""
    except Exception:
        message = str(exc)

    combined = f"{reason} {message}".lower()
    if "accessnotconfigured" in combined or "has not been used" in combined or "disabled" in combined:
        return (
            "Gmail API is disabled for this Google Cloud project. Enable Gmail API in Google Cloud Console, "
            "wait a minute for propagation, then retry sending."
        )
    if status == 401:
        return "Gmail authorization expired. Reconnect Gmail, then retry sending."
    if status == 403:
        return f"Gmail rejected the send: {message or reason or 'permission denied'}"
    return f"Gmail send failed: {message or reason or 'unknown Google API error'}"


def _allow_recipient(recipient: str):
    allowlist = [item.strip().lower() for item in os.getenv("EMAIL_ALLOWLIST", "").split(",") if item.strip()]
    if not allowlist:
        return
    lowered = recipient.lower()
    domain = lowered.split("@")[-1] if "@" in lowered else lowered
    if "*" in allowlist or lowered in allowlist or domain in allowlist or f"@{domain}" in allowlist:
        return
    raise HTTPException(
        status_code=403,
        detail=f"{recipient} is not in EMAIL_ALLOWLIST.",
    )


def _resolve_recipient(pitch: models.Pitch, db: Session) -> str:
    if os.getenv("GMAIL_TEST_RECIPIENT"):
        return os.getenv("GMAIL_TEST_RECIPIENT", "").strip()
    if pitch.recipient_email:
        return pitch.recipient_email
    venue = (
        db.query(models.Venue)
        .filter(models.Venue.entertainer_id == pitch.entertainer_id)
        .filter(models.Venue.name == pitch.venue_name)
        .order_by(models.Venue.created_at.desc())
        .first()
    )
    if venue and venue.contact_email:
        pitch.recipient_email = venue.contact_email
        return venue.contact_email
    raise HTTPException(
        status_code=400,
        detail="No recipient email on this pitch. Add recipient_email or set GMAIL_TEST_RECIPIENT.",
    )


def _account_credentials(account: models.GmailAccount, db: Session):
    try:
        from google.auth.transport.requests import Request as GoogleAuthRequest
        from google.oauth2.credentials import Credentials
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail="Gmail dependencies are missing. Run: pip install -r requirements.txt",
        ) from exc

    creds = Credentials(
        token=account.access_token,
        refresh_token=account.refresh_token,
        token_uri=account.token_uri,
        client_id=account.client_id or os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=account.client_secret or os.getenv("GOOGLE_CLIENT_SECRET"),
        scopes=json.loads(account.scopes or "[]"),
    )
    creds.expiry = account.expiry

    if creds.expired and creds.refresh_token:
        creds.refresh(GoogleAuthRequest())
        account.access_token = creds.token
        account.refresh_token = creds.refresh_token or account.refresh_token
        account.expiry = creds.expiry
        db.commit()

    if not creds.valid:
        raise HTTPException(status_code=401, detail="Gmail connection expired. Reconnect Google.")
    return creds


def _active_account(entertainer_id: str, db: Session) -> Optional[models.GmailAccount]:
    return (
        db.query(models.GmailAccount)
        .filter(models.GmailAccount.entertainer_id == entertainer_id)
        .filter(models.GmailAccount.is_active.is_(True))
        .order_by(models.GmailAccount.created_at.desc())
        .first()
    )


def _mark_pitch_sent(
    pitch: models.Pitch,
    db: Session,
    message_id: Optional[str] = None,
    thread_id: Optional[str] = None,
    update_initial_message: bool = True,
):
    pitch.status = "booked" if pitch.response_type == "accepted" or pitch.status == "booked" else "sent"
    pitch.sent_at = pitch.sent_at or datetime.utcnow()
    if message_id:
        pitch.gmail_message_id = message_id
    if thread_id:
        pitch.gmail_thread_id = thread_id
    conv = db.query(models.Conversation).filter(models.Conversation.pitch_id == pitch.id).first()
    if conv and update_initial_message:
        outbound = (
            db.query(models.ConversationMessage)
            .filter(models.ConversationMessage.conversation_id == conv.id)
            .filter(models.ConversationMessage.direction == "outbound")
            .filter(models.ConversationMessage.message_type == "initial_pitch")
            .order_by(models.ConversationMessage.created_at.asc())
            .first()
        )
        if outbound:
            outbound.subject = pitch.pitch_subject or outbound.subject
            outbound.body = pitch.pitch_body or outbound.body
            outbound.gmail_message_id = message_id or outbound.gmail_message_id
            outbound.gmail_thread_id = thread_id or outbound.gmail_thread_id
            outbound.created_at = pitch.sent_at or outbound.created_at
        else:
            db.add(models.ConversationMessage(
                conversation_id=conv.id,
                direction="outbound",
                message_type="initial_pitch",
                subject=pitch.pitch_subject,
                body=pitch.pitch_body or "",
                gmail_message_id=message_id,
                gmail_thread_id=thread_id,
                created_at=pitch.sent_at,
            ))
    db.commit()


async def _broadcast_event(db: Session, event: dict):
    await manager.broadcast(event)
    db.add(models.AgentEvent(
        agent_id=event.get("agent_id", "unknown"),
        event_type=event.get("event_type", "unknown"),
        message=event.get("message", ""),
        entertainer_id=event.get("entertainer_id"),
        target_id=event.get("target_id"),
        conclusion=event.get("conclusion"),
        extra=json.dumps({k: v for k, v in event.items() if k not in (
            "agent_id", "event_type", "message", "entertainer_id", "target_id", "conclusion"
        )}),
    ))
    db.commit()
    mirror_agent_event(event)


def _conversation_for_pitch(pitch: models.Pitch, db: Session) -> models.Conversation:
    conv = db.query(models.Conversation).filter(models.Conversation.pitch_id == pitch.id).first()
    if conv:
        return conv

    conv = models.Conversation(
        entertainer_id=pitch.entertainer_id,
        pitch_id=pitch.id,
        venue_name=pitch.venue_name,
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)

    if pitch.pitch_body:
        db.add(models.ConversationMessage(
            conversation_id=conv.id,
            direction="outbound",
            message_type="initial_pitch",
            subject=pitch.pitch_subject,
            body=pitch.pitch_body,
            gmail_message_id=pitch.gmail_message_id,
            gmail_thread_id=pitch.gmail_thread_id,
        ))
        db.commit()
    return conv


def _message_header(message: dict, name: str) -> str:
    headers = (message.get("payload") or {}).get("headers") or []
    for header in headers:
        if str(header.get("name", "")).lower() == name.lower():
            return header.get("value") or ""
    return ""


def _sender_email(message: dict) -> str:
    return parseaddr(_message_header(message, "From"))[1].lower()


def _message_datetime(message: dict) -> datetime:
    try:
        internal_ms = int(message.get("internalDate") or 0)
    except (TypeError, ValueError):
        internal_ms = 0
    if internal_ms:
        return datetime.utcfromtimestamp(internal_ms / 1000)
    return datetime.utcnow()


def _decode_gmail_data(data: Optional[str]) -> str:
    if not data:
        return ""
    padded = data + ("=" * (-len(data) % 4))
    try:
        return base64.urlsafe_b64decode(padded.encode()).decode("utf-8", errors="replace")
    except Exception:
        return ""


def _clean_html(raw: str) -> str:
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", raw)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</p>", "\n", text)
    text = re.sub(r"<[^>]+>", " ", text)
    return html.unescape(text)


def _clean_reply_body(raw: str) -> str:
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    text = re.split(r"\nOn .+ wrote:\n", text, maxsplit=1)[0]
    text = re.split(r"\n-{2,}\s*Original Message\s*-{2,}", text, maxsplit=1, flags=re.IGNORECASE)[0]
    lines = [line.rstrip() for line in text.split("\n") if not line.strip().startswith(">")]
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _payload_text(payload: dict) -> tuple[str, str]:
    mime_type = payload.get("mimeType") or ""
    body = payload.get("body") or {}
    data = body.get("data")
    if data and mime_type == "text/plain":
        return _decode_gmail_data(data), ""
    if data and mime_type == "text/html":
        return "", _clean_html(_decode_gmail_data(data))

    plain_parts = []
    html_parts = []
    for part in payload.get("parts") or []:
        plain, html_text = _payload_text(part)
        if plain:
            plain_parts.append(plain)
        if html_text:
            html_parts.append(html_text)
    return "\n".join(plain_parts), "\n".join(html_parts)


def _message_body(message: dict) -> str:
    plain, html_text = _payload_text(message.get("payload") or {})
    return _clean_reply_body(plain or html_text)


def _conversation_messages_payload(db: Session, conv: models.Conversation) -> list[dict]:
    return shared_conversation_messages_payload(db, conv)


def _latest_conversation_message(db: Session, conv: models.Conversation) -> Optional[models.ConversationMessage]:
    return (
        db.query(models.ConversationMessage)
        .filter(models.ConversationMessage.conversation_id == conv.id)
        .order_by(models.ConversationMessage.created_at.desc())
        .first()
    )


def _final_thank_you_already_sent(db: Session, conv: models.Conversation) -> bool:
    return db.query(models.ConversationMessage).filter(
        models.ConversationMessage.conversation_id == conv.id,
        models.ConversationMessage.direction == "outbound",
        models.ConversationMessage.message_type == "gmail_final_thanks_sent",
    ).first() is not None


def _memory_rate_as_float(memory: dict) -> Optional[float]:
    raw = str(memory.get("agreed_rate") or "").strip()
    if not raw:
        return None
    try:
        return float(re.sub(r"[^0-9.]", "", raw))
    except ValueError:
        return None


def _update_booking_from_memory(db: Session, booking: models.Booking, pitch: models.Pitch, memory: dict):
    agreed_rate = _memory_rate_as_float(memory)
    if agreed_rate and memory.get("rate_from_thread"):
        booking.agreed_rate = agreed_rate
        pitch.negotiated_price = agreed_rate
    date_mentions = memory.get("date_mentions") or []
    if date_mentions:
        booking.show_date = date_mentions[-1]
    agreements = memory.get("agreements") or []
    if agreements:
        booking.show_summary = "; ".join(str(item) for item in agreements)
    db.commit()
    apply_auto_logistics_to_booking(db, booking)


def _venue_payload_for_pitch(db: Session, pitch: models.Pitch, conv: Optional[models.Conversation] = None) -> dict:
    venue = None
    if pitch.venue_id:
        venue = db.query(models.Venue).filter(models.Venue.id == pitch.venue_id).first()
    if not venue and pitch.venue_name:
        venue = (
            db.query(models.Venue)
            .filter(models.Venue.entertainer_id == pitch.entertainer_id)
            .filter(models.Venue.name == pitch.venue_name)
            .order_by(models.Venue.created_at.desc())
            .first()
        )
    return {
        "name": (venue.name if venue else None) or (conv.venue_name if conv else None) or pitch.venue_name,
        "contact_name": venue.contact_name if venue else None,
        "contact_email": (venue.contact_email if venue else None) or pitch.recipient_email,
        "venue_type": venue.venue_type if venue else None,
        "contact_approach": venue.contact_approach if venue else pitch.venue_contact_approach,
        "why_fits": venue.why_fits if venue else None,
        "specific_examples": venue.specific_examples if venue else None,
    }


def _entertainer_payload(db: Session, entertainer_id: str) -> dict:
    entertainer = db.query(models.Entertainer).filter(models.Entertainer.id == entertainer_id).first()
    return {
        "id": entertainer.id,
        "name": entertainer.name,
        "type": entertainer.type,
        "genre": entertainer.genre,
        "location": entertainer.location,
        "experience_years": entertainer.experience_years,
        "social_followers": entertainer.social_followers,
        "highlights": entertainer.highlights,
        "current_rate": entertainer.current_rate,
    } if entertainer else {}


def _pitch_payload(pitch: models.Pitch) -> dict:
    return {
        "id": pitch.id,
        "venue_name": pitch.venue_name,
        "recipient_email": pitch.recipient_email,
        "pitch_subject": pitch.pitch_subject,
        "pitch_body": pitch.pitch_body,
        "proposed_rate": pitch.proposed_rate,
        "response_type": pitch.response_type,
    }


def _final_thank_you_draft(
    entertainer: dict,
    venue: dict,
    pitch: models.Pitch,
    memory: dict,
    outcome: str,
) -> dict:
    artist_name = entertainer.get("name") or "the artist"
    venue_name = venue.get("name") or pitch.venue_name or "your team"
    greeting = greeting_for(venue, _pitch_payload(pitch))
    subject = pitch.pitch_subject or f"Booking inquiry for {venue_name}"
    if not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"

    date_mentions = memory.get("date_mentions") or []
    date_line = f" We have the date noted as {date_mentions[-1]}." if date_mentions else ""
    rate = memory.get("agreed_rate")
    rate_line = f" We also have the rate noted as {rate}." if rate else ""

    if outcome == "rejected":
        body = (
            f"{greeting}\n\n"
            f"Thanks for letting us know. We appreciate you taking a look at {artist_name}.\n\n"
            "Let us know if you are interested in a future date or if a performance slot opens up later in the season.\n\n"
        )
    else:
        body = (
            f"{greeting}\n\n"
            f"Thanks for confirming. We appreciate you working with {artist_name}'s team."
            f"{date_line}{rate_line}\n\n"
            "We have everything noted on our end and will keep an eye out for any formal logistics you send over.\n\n"
        )

    return {
        "subject": remove_long_dashes(subject),
        "body": remove_long_dashes(ensure_team_signoff(body, str(entertainer.get("name") or "The Artist"))),
    }


def _analysis_for_reply(reply_body: str, venue_name: str, memory: Optional[dict] = None) -> dict:
    memory = memory or {}
    reply_lower = reply_body.lower()
    has_specific_date = reply_has_specific_date(reply_body)
    has_thread_date = bool(memory.get("date_mentions") or has_specific_date)
    rate_ok = bool(memory.get("rate_is_acceptable"))
    rate_below = bool(memory.get("rate_is_below_flexible_range"))
    price_guidance = memory.get("price_guidance") or ""
    is_success = any(w in reply_lower for w in [
        "confirmed", "booked", "let's book", "lets book", "let's do it", "lets do it",
        "we'd like to book", "we would like to book", "we want to book", "move forward",
        "lock it in", "lock in", "works for us", "sounds good", "deal", "approved",
        "love to have", "happy to book",
    ])
    is_interested = any(w in reply_lower for w in [
        "interested", "available", "love to learn", "send over", "send the reel", "more info",
    ])
    is_rejected = any(w in reply_lower for w in [
        "not interested", "no thanks", "pass", "decline", "fully booked", "not a fit",
    ])
    is_budget = any(w in reply_lower for w in ["budget", "rate", "price", "cost", "fee", "$"])
    is_question = "?" in reply_body

    if is_rejected:
        interest = "low"
        response_type = "rejected"
        likelihood = 1.5
        worked = "The outreach reached the right surface area, but this target is not ready right now."
        next_action = "Thank them, leave the door open, and do not keep pushing this thread."
    elif rate_below:
        interest = "medium"
        response_type = "negotiating"
        likelihood = 5.4
        worked = "The venue engaged on price, but the counter is below the artist's flexible floor."
        next_action = f"Counter once using the pricing floor. {price_guidance}".strip()
    elif is_success or (has_thread_date and rate_ok and not is_question):
        interest = "high"
        response_type = "accepted"
        likelihood = 8.2
        worked = "The venue gave enough booking signal and the price is within the allowed flexible range."
        next_action = "Move this into secured deals. Do not keep emailing unless the venue asks a direct blocker question."
    elif has_thread_date and rate_ok:
        interest = "high"
        response_type = "accepted"
        likelihood = 7.6
        worked = "The venue supplied a concrete date and the price is inside the acceptable range."
        next_action = "Send one concise answer only if they asked a direct question, then stop outreach."
    elif is_budget:
        interest = "medium"
        response_type = "negotiating"
        likelihood = 5.8
        worked = "The venue is engaging on logistics or price, which suggests there is real consideration."
        next_action = "Acknowledge the proposed date and answer the pricing question directly." if has_specific_date else "Answer the pricing question directly and offer a simple package or flexible set length."
    elif has_specific_date:
        interest = "high"
        response_type = "maybe"
        likelihood = 6.8
        worked = "The venue supplied a concrete date, so the conversation should move to logistics instead of asking for dates again."
        next_action = "Acknowledge the date and ask only for missing logistics like set time, load-in, set length, and payment details."
    elif is_interested or is_question:
        interest = "medium"
        response_type = "maybe"
        likelihood = 6.0 if is_interested else 5.0
        worked = "The reply asks for more context, meaning the pitch earned consideration."
        next_action = "Answer the question, include one proof point, and make the next step easy."
    else:
        interest = "medium"
        response_type = "maybe"
        likelihood = 4.0
        worked = "The pitch generated a response and opened a conversation."
        next_action = "Follow up with a concise proof point, rate, and availability."

    return {
        "interest_level": interest,
        "response_type": response_type,
        "signals": [
            f"Reply received from {venue_name}",
            "Confirmed booking language detected" if response_type == "accepted" else "Specific date detected" if has_specific_date else "Needs follow-up clarification",
        ],
        "what_worked": worked,
        "what_to_do_next": next_action,
        "conversion_likelihood": likelihood,
        "thinking_steps": [
            {"step": f"Reading Gmail reply from {venue_name}...", "conclusion": f"Detected {interest} interest"},
            {"step": "Classifying booking signal...", "conclusion": response_type.replace("_", " ")},
            {"step": "Choosing next action...", "conclusion": next_action},
        ],
    }


async def _analyze_imported_reply(db: Session, conv: models.Conversation, pitch: models.Pitch, reply_body: str):
    entertainer = db.query(models.Entertainer).filter(models.Entertainer.id == pitch.entertainer_id).first()
    entertainer_payload = {
        "id": entertainer.id,
        "name": entertainer.name,
        "type": entertainer.type,
        "genre": entertainer.genre,
        "location": entertainer.location,
        "experience_years": entertainer.experience_years,
        "social_followers": entertainer.social_followers,
        "highlights": entertainer.highlights,
        "current_rate": entertainer.current_rate,
    } if entertainer else {}
    memory = build_conversation_memory(
        _conversation_messages_payload(db, conv),
        reply_body,
        {
            "venue_name": pitch.venue_name,
            "recipient_email": pitch.recipient_email,
            "proposed_rate": pitch.proposed_rate,
        },
        entertainer_payload,
    )
    analysis = _analysis_for_reply(reply_body, conv.venue_name or pitch.venue_name or "venue", memory)
    completion = conversation_completion_status(memory, analysis, reply_body)
    await _broadcast_event(db, {
        "agent_id": "agent3",
        "event_type": "working",
        "message": f"Analyzing Gmail reply from {conv.venue_name}",
        "entertainer_id": pitch.entertainer_id,
        "target_id": conv.id,
    })
    for thought in analysis["thinking_steps"]:
        await _broadcast_event(db, {
            "agent_id": "agent3",
            "event_type": "thinking",
            "message": thought["step"],
            "conclusion": thought["conclusion"],
            "entertainer_id": pitch.entertainer_id,
            "target_id": conv.id,
        })

    conv.interest_level = analysis["interest_level"]
    conv.signals = json.dumps(analysis["signals"])
    conv.what_worked = analysis["what_worked"]
    conv.what_to_do_next = completion["reason"] if completion.get("stop_outreach") else analysis["what_to_do_next"]
    conv.conversion_likelihood = analysis["conversion_likelihood"]
    pitch.status = "rejected" if analysis["response_type"] == "rejected" else "responded"
    pitch.response_type = analysis["response_type"]
    db.commit()

    if analysis["response_type"] == "accepted":
        booking, created = ensure_booking_for_pitch(db, pitch, conv)
        _update_booking_from_memory(db, booking, pitch, memory)
        if completion.get("stop_outreach"):
            booking.conversation_stage = "secured"
            booking.show_summary = (booking.show_summary or "") + f"; Outreach complete: {completion['reason']}"
            db.commit()
        await _broadcast_event(db, {
            "agent_id": "agent2",
            "event_type": "deal_secured",
            "message": f"Accepted reply from {conv.venue_name}; secured deal added to Pipeline.",
            "entertainer_id": pitch.entertainer_id,
            "target_id": conv.id,
            "pitch_id": pitch.id,
            "booking_id": booking.id,
            "created": created,
        })
        await _broadcast_event(db, {
            "agent_id": "agent4",
            "event_type": "booking_secured",
            "message": f"Pipeline is now tracking secured deal with {conv.venue_name}.",
            "entertainer_id": pitch.entertainer_id,
            "target_id": conv.id,
            "pitch_id": pitch.id,
            "booking_id": booking.id,
            "created": created,
        })

    await _broadcast_event(db, {
        "agent_id": "agent3",
        "event_type": "insight",
        "message": analysis["what_worked"],
        "entertainer_id": pitch.entertainer_id,
        "target_id": conv.id,
        "interest_level": analysis["interest_level"],
        "next_action": analysis["what_to_do_next"],
        "conversion_likelihood": analysis["conversion_likelihood"],
    })
    analysis["completion"] = completion
    analysis["memory"] = memory
    return analysis


async def _broadcast_outreach_complete(
    db: Session,
    conv: models.Conversation,
    pitch: models.Pitch,
    completion: dict,
    response_type: str,
    final_status: str,
):
    await _broadcast_event(db, {
        "agent_id": "agent2",
        "event_type": "outreach_complete",
        "message": f"Marked {conv.venue_name} done. Final thank-you status: {final_status}. {completion.get('reason')}",
        "entertainer_id": pitch.entertainer_id,
        "target_id": conv.id,
        "pitch_id": pitch.id,
        "response_type": response_type,
        "final_thank_you_status": final_status,
    })


async def _send_final_thank_you_if_needed(
    db: Session,
    conv: models.Conversation,
    pitch: models.Pitch,
    memory: dict,
    analysis: dict,
    completion: dict,
    service=None,
    account: Optional[models.GmailAccount] = None,
) -> dict:
    if _final_thank_you_already_sent(db, conv):
        return {"ok": True, "sent": False, "already_sent": True, "final_status": "already sent"}

    latest = _latest_conversation_message(db, conv)
    if latest and latest.direction == "outbound":
        return {"ok": True, "sent": False, "already_outbound": True, "final_status": "already outbound"}

    entertainer_payload = _entertainer_payload(db, pitch.entertainer_id)
    venue_payload = _venue_payload_for_pitch(db, pitch, conv)
    outcome = str(completion.get("outcome") or analysis.get("response_type") or pitch.response_type or "accepted").lower()
    draft = _final_thank_you_draft(entertainer_payload, venue_payload, pitch, memory, outcome)
    pitch.pitch_subject = draft["subject"]
    pitch.pitch_body = draft["body"]
    pitch.strategy_note = "Final thank-you sent before closing the thread."
    db.commit()

    try:
        sent_result = _send_pitch_with_gmail_core(
            pitch,
            db,
            service=service,
            account=account,
            sent_message_type="gmail_final_thanks_sent",
        )
    except Exception as exc:
        await _broadcast_event(db, {
            "agent_id": "agent2",
            "event_type": "error",
            "message": f"Could not send final thank-you to {conv.venue_name}: {exc}",
            "entertainer_id": pitch.entertainer_id,
            "target_id": conv.id,
            "pitch_id": pitch.id,
        })
        return {"ok": False, "sent": False, "draft_created": True, "final_status": "send failed"}

    await _broadcast_event(db, {
        "agent_id": "agent2",
        "event_type": "gmail_final_thanks_sent",
        "message": f"Sent final thank-you to {conv.venue_name}; recipient no longer has the last message.",
        "entertainer_id": pitch.entertainer_id,
        "target_id": conv.id,
        "pitch_id": pitch.id,
        "message_id": sent_result.get("message_id"),
        "thread_id": sent_result.get("thread_id"),
        "dry_run": sent_result.get("dry_run", False),
    })
    return {
        "ok": True,
        "sent": True,
        "draft_created": True,
        "dry_run": sent_result.get("dry_run", False),
        "final_status": "sent",
    }


async def _ensure_final_thank_you_for_closed_thread(
    db: Session,
    conv: models.Conversation,
    pitch: models.Pitch,
    service=None,
    account: Optional[models.GmailAccount] = None,
) -> dict:
    latest = _latest_conversation_message(db, conv)
    if not latest or latest.direction != "inbound" or _final_thank_you_already_sent(db, conv):
        return {"ok": True, "sent": False, "final_status": "not needed"}

    response_type = str(pitch.response_type or "").lower()
    if response_type not in {"accepted", "rejected"} and pitch.status not in {"booked", "rejected"}:
        return {"ok": True, "sent": False, "final_status": "thread still open"}

    entertainer_payload = _entertainer_payload(db, pitch.entertainer_id)
    memory = build_conversation_memory(
        _conversation_messages_payload(db, conv),
        latest.body,
        {
            "venue_name": pitch.venue_name,
            "recipient_email": pitch.recipient_email,
            "proposed_rate": pitch.proposed_rate,
        },
        entertainer_payload,
    )
    analysis = {
        "response_type": "accepted" if response_type == "accepted" or pitch.status == "booked" else "rejected",
    }
    completion = conversation_completion_status(memory, analysis, latest.body)
    if not completion.get("stop_outreach"):
        return {"ok": True, "sent": False, "final_status": "thread still needs response"}

    result = await _send_final_thank_you_if_needed(
        db,
        conv,
        pitch,
        memory,
        analysis,
        completion,
        service=service,
        account=account,
    )
    await _broadcast_outreach_complete(
        db,
        conv,
        pitch,
        completion,
        analysis["response_type"],
        result.get("final_status", "unknown"),
    )
    return result


async def _generate_reply_draft_for_latest_reply(
    db: Session,
    conv: models.Conversation,
    pitch: models.Pitch,
    latest_reply: str,
    analysis: dict,
) -> dict:
    entertainer = db.query(models.Entertainer).filter(models.Entertainer.id == pitch.entertainer_id).first()
    if not entertainer:
        return {"ok": False, "reason": "missing_entertainer"}

    venue = None
    if pitch.venue_id:
        venue = db.query(models.Venue).filter(models.Venue.id == pitch.venue_id).first()
    if not venue and pitch.venue_name:
        venue = (
            db.query(models.Venue)
            .filter(models.Venue.entertainer_id == pitch.entertainer_id)
            .filter(models.Venue.name == pitch.venue_name)
            .order_by(models.Venue.created_at.desc())
            .first()
        )

    entertainer_payload = {
        "id": entertainer.id,
        "name": entertainer.name,
        "type": entertainer.type,
        "genre": entertainer.genre,
        "location": entertainer.location,
        "experience_years": entertainer.experience_years,
        "social_followers": entertainer.social_followers,
        "highlights": entertainer.highlights,
        "current_rate": entertainer.current_rate,
    }
    venue_payload = {
        "name": (venue.name if venue else None) or conv.venue_name or pitch.venue_name,
        "contact_name": venue.contact_name if venue else None,
        "contact_email": (venue.contact_email if venue else None) or pitch.recipient_email,
        "venue_type": venue.venue_type if venue else None,
        "contact_approach": venue.contact_approach if venue else pitch.venue_contact_approach,
        "why_fits": venue.why_fits if venue else None,
        "specific_examples": venue.specific_examples if venue else None,
    }
    pitch_payload = {
        "id": pitch.id,
        "venue_name": pitch.venue_name,
        "recipient_email": pitch.recipient_email,
        "pitch_subject": pitch.pitch_subject,
        "pitch_body": pitch.pitch_body,
        "proposed_rate": pitch.proposed_rate,
        "response_type": pitch.response_type,
    }
    draft = generate_reply_draft(
        entertainer_payload,
        venue_payload,
        pitch_payload,
        latest_reply,
        analysis,
        conversation_messages=_conversation_messages_payload(db, conv),
        prior_context=prior_venue_context(
            db,
            pitch.entertainer_id,
            venue_payload.get("name") or conv.venue_name or pitch.venue_name,
            contact_email=venue_payload.get("contact_email") or pitch.recipient_email,
            exclude_conversation_id=conv.id,
            exclude_pitch_id=pitch.id,
        ),
    )
    pitch.pitch_subject = remove_long_dashes(draft["subject"])
    pitch.pitch_body = remove_long_dashes(draft["body"])
    pitch.strategy_note = "Auto-generated reply draft from latest Gmail response."
    db.commit()

    await _broadcast_event(db, {
        "agent_id": "agent2",
        "event_type": "pitch_ready",
        "message": f"Generated reply draft for {conv.venue_name} from latest Gmail response.",
        "entertainer_id": pitch.entertainer_id,
        "target_id": conv.id,
        "pitch_id": pitch.id,
        "generation_source": draft.get("generation_source"),
    })
    return {"ok": True, "generation_source": draft.get("generation_source")}


@router.get("/status")
def gmail_status(entertainer_id: str, db: Session = Depends(get_db)):
    account = _active_account(entertainer_id, db)
    return {
        "configured": bool(os.getenv("GOOGLE_CLIENT_ID") and os.getenv("GOOGLE_CLIENT_SECRET")),
        "connected": bool(account),
        "email": account.email_address if account else None,
        "live_sends": _bool_env("GMAIL_LIVE_SENDS", False),
        "read_sync_enabled": _has_read_scope(account),
        "last_sync_at": account.last_sync_at.isoformat() if account and account.last_sync_at else None,
    }


@router.get("/auth-url")
def gmail_auth_url(
    entertainer_id: str,
    return_to: str = Query("/onboarding?gmail=connected"),
):
    state = _sign_oauth_state({
        "entertainer_id": entertainer_id,
        "return_to": _safe_return_to(return_to),
        "nonce": secrets.token_urlsafe(12),
        "exp": int(time.time()) + 3600,
    })
    flow = _build_flow(state=state)
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return {"auth_url": auth_url}


@router.get("/oauth2callback")
def gmail_oauth_callback(request: FastAPIRequest, db: Session = Depends(get_db)):
    if request.query_params.get("error"):
        raise HTTPException(
            status_code=400,
            detail=f"Google OAuth error: {request.query_params.get('error_description') or request.query_params.get('error')}",
        )

    state = request.query_params.get("state", "")
    state_payload = _verify_oauth_state(state) or _oauth_states.pop(state, None)
    entertainer_id = state_payload.get("entertainer_id") if state_payload else None
    if not entertainer_id:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state. Start Gmail connection again.")

    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Google OAuth callback did not include an authorization code.")
    token_data = _exchange_oauth_code(code)

    email_address = None
    try:
        resp = httpx.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
            timeout=10,
        )
        if resp.status_code == 200:
            email_address = resp.json().get("email")
    except Exception:
        email_address = None

    account = (
        db.query(models.GmailAccount)
        .filter(models.GmailAccount.entertainer_id == entertainer_id)
        .filter(models.GmailAccount.is_active.is_(True))
        .first()
    )
    if not account:
        account = models.GmailAccount(entertainer_id=entertainer_id, access_token=token_data["access_token"])
        db.add(account)

    account.email_address = email_address
    account.access_token = token_data["access_token"]
    account.refresh_token = token_data.get("refresh_token") or account.refresh_token
    account.token_uri = "https://oauth2.googleapis.com/token"
    account.client_id = os.getenv("GOOGLE_CLIENT_ID")
    account.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    account.scopes = json.dumps((token_data.get("scope") or " ".join(SCOPES)).split())
    account.expiry = datetime.utcnow() + timedelta(seconds=int(token_data.get("expires_in") or 3600))
    account.is_active = True
    db.commit()

    return RedirectResponse(f"{_frontend_url()}{_safe_return_to(state_payload.get('return_to') if state_payload else None)}")


@router.post("/send-pitch/{pitch_id}")
def send_pitch_with_gmail(pitch_id: str, db: Session = Depends(get_db)):
    pitch = db.query(models.Pitch).filter(models.Pitch.id == pitch_id).first()
    if not pitch:
        raise HTTPException(status_code=404, detail="Pitch not found")
    return _send_pitch_with_gmail_core(pitch, db)


def _send_pitch_with_gmail_core(
    pitch: models.Pitch,
    db: Session,
    service=None,
    account: Optional[models.GmailAccount] = None,
    sent_message_type: str = "gmail_reply_sent",
):
    is_thread_reply = bool(
        pitch.gmail_thread_id
        and pitch.gmail_thread_id != "dry-run"
        and (pitch.response_type or pitch.status == "responded")
    )
    subject = pitch.pitch_subject or f"Booking inquiry for {pitch.venue_name}"
    if is_thread_reply and not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"

    dry_run = not _bool_env("GMAIL_LIVE_SENDS", False)
    if dry_run:
        if is_thread_reply:
            conv = _conversation_for_pitch(pitch, db)
            db.add(models.ConversationMessage(
                conversation_id=conv.id,
                direction="outbound",
                message_type=sent_message_type,
                subject=subject,
                body=pitch.pitch_body or "",
                gmail_message_id="dry-run",
                gmail_thread_id=pitch.gmail_thread_id,
            ))
            db.commit()
        _mark_pitch_sent(
            pitch,
            db,
            message_id="dry-run",
            thread_id=pitch.gmail_thread_id if is_thread_reply else "dry-run",
            update_initial_message=not is_thread_reply,
        )
        mirror_pitch_sent(pitch, dry_run=True, source="gmail_dry_run")
        return {"ok": True, "dry_run": True, "message": "GMAIL_LIVE_SENDS is false; pitch marked sent without emailing."}

    recipient = _resolve_recipient(pitch, db)
    _allow_recipient(recipient)

    account = account or _active_account(pitch.entertainer_id, db)
    if not account:
        raise HTTPException(status_code=401, detail="No connected Gmail account. Connect Google first.")

    try:
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail="Gmail dependencies are missing. Run: pip install -r requirements.txt",
        ) from exc

    email = EmailMessage()
    email["To"] = recipient
    if account.email_address:
        email["From"] = account.email_address
    email["Subject"] = subject
    email.set_content(pitch.pitch_body or "")

    raw = base64.urlsafe_b64encode(email.as_bytes()).decode()
    service = service or build("gmail", "v1", credentials=_account_credentials(account, db))
    send_body = {"raw": raw}
    if is_thread_reply:
        send_body["threadId"] = pitch.gmail_thread_id
    try:
        sent = service.users().messages().send(userId="me", body=send_body).execute()
    except HttpError as exc:
        raise HTTPException(
            status_code=getattr(getattr(exc, "resp", None), "status", 502) or 502,
            detail=_gmail_http_error_detail(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Gmail send failed: {exc}") from exc

    if is_thread_reply:
        conv = _conversation_for_pitch(pitch, db)
        db.add(models.ConversationMessage(
            conversation_id=conv.id,
            direction="outbound",
            message_type=sent_message_type,
            subject=subject,
            body=pitch.pitch_body or "",
            gmail_message_id=sent.get("id"),
            gmail_thread_id=sent.get("threadId") or pitch.gmail_thread_id,
        ))
        db.commit()

    _mark_pitch_sent(
        pitch,
        db,
        message_id=sent.get("id"),
        thread_id=sent.get("threadId"),
        update_initial_message=not is_thread_reply,
    )
    mirror_pitch_sent(pitch, recipient=recipient, dry_run=False, source="gmail_live")
    return {
        "ok": True,
        "dry_run": False,
        "recipient": recipient,
        "message_id": sent.get("id"),
        "thread_id": sent.get("threadId"),
    }


@router.post("/sync-replies")
async def sync_gmail_replies(entertainer_id: str, db: Session = Depends(get_db)):
    account = _active_account(entertainer_id, db)
    if not account:
        raise HTTPException(status_code=401, detail="No connected Gmail account. Connect Gmail first.")
    if not _has_read_scope(account):
        raise HTTPException(
            status_code=403,
            detail="Gmail is connected for sending only. Reconnect Gmail to grant reply sync access.",
        )

    try:
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail="Gmail dependencies are missing. Run: pip install -r requirements.txt",
        ) from exc

    service = build("gmail", "v1", credentials=_account_credentials(account, db))
    account_email = (account.email_address or "").lower()
    pitches = (
        db.query(models.Pitch)
        .filter(models.Pitch.entertainer_id == entertainer_id)
        .filter(models.Pitch.gmail_thread_id.isnot(None))
        .all()
    )

    threads_checked = 0
    replies_imported = 0
    skipped_no_thread = 0
    reply_drafts_generated = 0
    auto_replies_sent = 0
    analyzed_targets: set[str] = set()

    await _broadcast_event(db, {
        "agent_id": "agent3",
        "event_type": "working",
        "message": "Syncing Gmail inbox replies...",
        "entertainer_id": entertainer_id,
    })

    for pitch in pitches:
        if not pitch.gmail_thread_id or pitch.gmail_thread_id == "dry-run":
            skipped_no_thread += 1
            continue
        threads_checked += 1
        try:
            thread = service.users().threads().get(
                userId="me",
                id=pitch.gmail_thread_id,
                format="full",
            ).execute()
        except Exception as exc:
            await _broadcast_event(db, {
                "agent_id": "agent3",
                "event_type": "error",
                "message": f"Could not sync Gmail thread for {pitch.venue_name}: {exc}",
                "entertainer_id": entertainer_id,
            })
            continue

        conv = _conversation_for_pitch(pitch, db)
        thread_messages = sorted(thread.get("messages") or [], key=_message_datetime)
        for message in thread_messages:
            message_id = message.get("id")
            if not message_id or message_id == pitch.gmail_message_id:
                continue
            if db.query(models.ConversationMessage).filter(
                models.ConversationMessage.gmail_message_id == message_id
            ).first():
                continue

            labels = set(message.get("labelIds") or [])
            from_email = _sender_email(message)
            if "SENT" in labels or (account_email and from_email == account_email):
                continue

            body = _message_body(message)
            if not body:
                continue

            db.add(models.ConversationMessage(
                conversation_id=conv.id,
                direction="inbound",
                message_type="gmail_reply",
                subject=_message_header(message, "Subject") or pitch.pitch_subject,
                body=body,
                sentiment=None,
                gmail_message_id=message_id,
                gmail_thread_id=message.get("threadId") or pitch.gmail_thread_id,
                from_email=from_email or None,
                created_at=_message_datetime(message),
            ))
            db.commit()
            replies_imported += 1
            analyzed_targets.add(conv.id)
            analysis = await _analyze_imported_reply(db, conv, pitch, body)
            completion = analysis.get("completion") or {}
            if completion.get("stop_outreach"):
                final_result = await _send_final_thank_you_if_needed(
                    db,
                    conv,
                    pitch,
                    analysis.get("memory") or {},
                    analysis,
                    completion,
                    service=service,
                    account=account,
                )
                if final_result.get("draft_created"):
                    reply_drafts_generated += 1
                if final_result.get("sent") and not final_result.get("dry_run"):
                    auto_replies_sent += 1
                await _broadcast_outreach_complete(
                    db,
                    conv,
                    pitch,
                    completion,
                    analysis.get("response_type") or pitch.response_type or "accepted",
                    final_result.get("final_status", "unknown"),
                )
                continue
            draft_result = await _generate_reply_draft_for_latest_reply(db, conv, pitch, body, analysis)
            if draft_result.get("ok"):
                reply_drafts_generated += 1
                entertainer = db.query(models.Entertainer).filter(models.Entertainer.id == pitch.entertainer_id).first()
                if entertainer and entertainer.outreach_mode == "auto_pitch":
                    try:
                        sent_result = _send_pitch_with_gmail_core(pitch, db, service=service, account=account)
                        auto_replies_sent += 0 if sent_result.get("dry_run") else 1
                        await _broadcast_event(db, {
                            "agent_id": "agent2",
                            "event_type": "gmail_auto_sent",
                            "message": f"Auto-sent Gmail reply to {conv.venue_name}.",
                            "entertainer_id": pitch.entertainer_id,
                            "target_id": conv.id,
                            "pitch_id": pitch.id,
                            "message_id": sent_result.get("message_id"),
                            "thread_id": sent_result.get("thread_id"),
                        })
                    except Exception as exc:
                        await _broadcast_event(db, {
                            "agent_id": "agent2",
                            "event_type": "error",
                            "message": f"Could not auto-send Gmail reply to {conv.venue_name}: {exc}",
                            "entertainer_id": pitch.entertainer_id,
                            "target_id": conv.id,
                            "pitch_id": pitch.id,
                        })

        final_result = await _ensure_final_thank_you_for_closed_thread(
            db,
            conv,
            pitch,
            service=service,
            account=account,
        )
        if final_result.get("draft_created"):
            reply_drafts_generated += 1
        if final_result.get("sent") and not final_result.get("dry_run"):
            auto_replies_sent += 1

    account.last_sync_at = datetime.utcnow()
    db.commit()

    await _broadcast_event(db, {
        "agent_id": "agent3",
        "event_type": "complete",
        "message": f"Gmail sync imported {replies_imported} replies, generated {reply_drafts_generated} drafts, and auto-sent {auto_replies_sent}.",
        "entertainer_id": entertainer_id,
        "threads_checked": threads_checked,
        "replies_imported": replies_imported,
        "reply_drafts_generated": reply_drafts_generated,
        "auto_replies_sent": auto_replies_sent,
    })

    return {
        "ok": True,
        "threads_checked": threads_checked,
        "replies_imported": replies_imported,
        "reply_drafts_generated": reply_drafts_generated,
        "auto_replies_sent": auto_replies_sent,
        "analyzed_conversations": len(analyzed_targets),
        "skipped_no_thread": skipped_no_thread,
        "last_sync_at": account.last_sync_at.isoformat() if account.last_sync_at else None,
    }
