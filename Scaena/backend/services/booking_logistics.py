from __future__ import annotations

from datetime import date, datetime
import json
import re
from typing import Any

from sqlalchemy.orm import Session

from backend import models
from backend.services.booking_pipeline import checklist_json, default_logistics_checklist
from backend.services.conversation_visibility import visible_conversation_messages


MONTHS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}


def _parse_checklist(raw: str | None) -> dict[str, bool]:
    checklist = default_logistics_checklist()
    if not raw:
        return checklist
    try:
        parsed = json.loads(raw)
    except Exception:
        return checklist
    if isinstance(parsed, dict):
        checklist.update({key: bool(value) for key, value in parsed.items() if key in checklist})
    return checklist


def _valid_date(year: int, month: int, day: int) -> str | None:
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return None


def _full_year(raw_year: str | None, default_year: int) -> int:
    if not raw_year:
        return default_year
    year = int(raw_year)
    if year < 100:
        return 2000 + year
    return year


def normalize_show_date(raw: str | None, *, today: date | None = None) -> str | None:
    """Normalize a date mention into YYYY-MM-DD.

    Dates without a year, such as 4/18 or Apr 18, intentionally resolve to the
    current calendar year. For demo conversations this avoids Agent 4 asking for
    confirmation after the venue already gave a date.
    """
    text = str(raw or "").strip()
    if not text:
        return None
    today = today or datetime.utcnow().date()

    iso = re.search(r"\b(20\d{2})[-/](0?[1-9]|1[0-2])[-/](0?[1-9]|[12]\d|3[01])\b", text)
    if iso:
        return _valid_date(int(iso.group(1)), int(iso.group(2)), int(iso.group(3)))

    # Use slash for no-year shorthand dates like 4/18. Bare hyphen values such
    # as 10-11 often mean time ranges, so hyphen dates require an explicit year.
    numeric = re.search(
        r"\b(0?[1-9]|1[0-2])/(0?[1-9]|[12]\d|3[01])(?:[/-](\d{2,4}))?\b"
        r"|\b(0?[1-9]|1[0-2])-(0?[1-9]|[12]\d|3[01])-(\d{2,4})\b",
        text,
    )
    if numeric:
        month = numeric.group(1) or numeric.group(4)
        day = numeric.group(2) or numeric.group(5)
        raw_year = numeric.group(3) or numeric.group(6)
        year = _full_year(raw_year, today.year)
        return _valid_date(year, int(month), int(day))

    month_name = re.search(
        r"\b("
        r"jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
        r"jul(?:y)?|aug(?:ust)?|sep(?:t|tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?"
        r")\.?\s+([0-9]{1,2})(?:st|nd|rd|th)?(?:,\s*(\d{2,4}))?\b",
        text,
        flags=re.I,
    )
    if month_name:
        month = MONTHS.get(month_name.group(1).lower().rstrip(".")[:3])
        if month_name.group(1).lower().startswith("sept"):
            month = 9
        if month:
            year = _full_year(month_name.group(3), today.year)
            return _valid_date(year, month, int(month_name.group(2)))

    return None


def _date_mentions(text: str) -> list[str]:
    patterns = [
        r"\b20\d{2}[-/](?:0?[1-9]|1[0-2])[-/](?:0?[1-9]|[12]\d|3[01])\b",
        r"\b(?:0?[1-9]|1[0-2])/(?:0?[1-9]|[12]\d|3[01])(?:[/-]\d{2,4})?\b",
        r"\b(?:0?[1-9]|1[0-2])-(?:0?[1-9]|[12]\d|3[01])-\d{2,4}\b",
        (
            r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
            r"jul(?:y)?|aug(?:ust)?|sep(?:t|tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
            r"\.?\s+[0-9]{1,2}(?:st|nd|rd|th)?(?:,\s*\d{2,4})?\b"
        ),
    ]
    mentions: list[str] = []
    for pattern in patterns:
        mentions.extend(match.group(0) for match in re.finditer(pattern, text, flags=re.I))
    return mentions


def _latest_show_date(text: str) -> str | None:
    normalized = [normalize_show_date(mention) for mention in _date_mentions(text)]
    normalized = [item for item in normalized if item]
    return normalized[-1] if normalized else None


def _latest_money_value(text: str) -> float | None:
    matches = list(re.finditer(r"\$\s*([0-9][0-9,]*(?:\.\d{1,2})?)", text))
    if not matches:
        return None

    contextual: list[re.Match[str]] = []
    for match in matches:
        left = text[max(0, match.start() - 60): match.start()].lower()
        right = text[match.end(): match.end() + 60].lower()
        if re.search(r"\b(rate|fee|budget|pay|paid|payment|payout|cost|price|offer|honorarium|invoice|deposit)\b", f"{left} {right}"):
            contextual.append(match)

    chosen = (contextual or matches)[-1]
    try:
        return float(chosen.group(1).replace(",", ""))
    except ValueError:
        return None


def _has(pattern: str, text: str) -> bool:
    return bool(re.search(pattern, text, flags=re.I))


def _conversation_for_booking(db: Session, booking: models.Booking) -> models.Conversation | None:
    if booking.target_id:
        conv = db.query(models.Conversation).filter(models.Conversation.id == booking.target_id).first()
        if conv:
            return conv
    if booking.pitch_id:
        return db.query(models.Conversation).filter(models.Conversation.pitch_id == booking.pitch_id).first()
    return None


def _thread_text(db: Session, booking: models.Booking) -> tuple[str, str, str]:
    conv = _conversation_for_booking(db, booking)
    visible = visible_conversation_messages(db, conv) if conv else []

    sent_booking_messages = (
        db.query(models.BookingMessage)
        .filter(models.BookingMessage.booking_id == booking.id)
        .filter(models.BookingMessage.status == "sent")
        .order_by(models.BookingMessage.created_at)
        .all()
    )

    inbound = "\n".join(msg.body or "" for msg in visible if msg.direction == "inbound")
    outbound_parts = [msg.body or "" for msg in visible if msg.direction == "outbound"]
    outbound_parts.extend(msg.body or "" for msg in sent_booking_messages)
    outbound = "\n".join(outbound_parts)
    return inbound, outbound, "\n".join(part for part in [inbound, outbound] if part)


def _summarize_changes(evidence: dict[str, Any]) -> str:
    labels = {
        "date_confirmed": "date",
        "rate_confirmed": "rate",
        "contact_confirmed": "contact",
        "set_length_confirmed": "set length",
        "load_in_confirmed": "load-in",
        "payment_confirmed": "payment",
        "promo_assets_sent": "promo assets",
        "contract_invoice_sent": "contract/invoice",
    }
    changed = [labels[key] for key in labels if evidence.get(key)]
    return ", ".join(changed)


def apply_auto_logistics_to_booking(db: Session, booking: models.Booking) -> tuple[bool, dict[str, Any]]:
    """Infer Agent 4 logistics from visible chat history and persist checklist updates."""
    inbound_text, outbound_text, all_text = _thread_text(db, booking)
    if not all_text.strip():
        return False, {}

    checklist = _parse_checklist(booking.logistics_checklist)
    before = {
        "checklist": dict(checklist),
        "show_date": booking.show_date,
        "agreed_rate": booking.agreed_rate,
        "stage": booking.conversation_stage,
    }

    inferred: dict[str, bool] = {}
    evidence: dict[str, Any] = {}

    show_date = _latest_show_date(inbound_text) or _latest_show_date(all_text)
    if show_date:
        booking.show_date = show_date
        inferred["date_confirmed"] = True
        evidence["date_confirmed"] = show_date
    elif booking.show_date and normalize_show_date(booking.show_date):
        booking.show_date = normalize_show_date(booking.show_date)
        inferred["date_confirmed"] = True
        evidence["date_confirmed"] = booking.show_date

    rate = _latest_money_value(inbound_text) or _latest_money_value(all_text)
    if rate is not None:
        booking.agreed_rate = rate
        inferred["rate_confirmed"] = True
        evidence["rate_confirmed"] = f"${rate:.0f}"
    elif booking.agreed_rate:
        inferred["rate_confirmed"] = True
        evidence["rate_confirmed"] = f"${booking.agreed_rate:.0f}"

    pitch = db.query(models.Pitch).filter(models.Pitch.id == booking.pitch_id).first() if booking.pitch_id else None
    if (pitch and pitch.recipient_email) or _has(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", all_text):
        inferred["contact_confirmed"] = True
        evidence["contact_confirmed"] = pitch.recipient_email if pitch and pitch.recipient_email else "email in thread"

    if _has(r"\b(set length|runtime|run time|performance length|(?:[1-9][0-9])\s*(?:minute|min)\s*(?:set|performance)?|half[- ]hour|one[- ]hour|hour[- ]long)\b", inbound_text):
        inferred["set_length_confirmed"] = True
        evidence["set_length_confirmed"] = "set length mentioned"

    if _has(r"\b(load[- ]?in|soundcheck|sound check|arrival|arrive by|arrive at|doors at|venue access)\b", inbound_text):
        inferred["load_in_confirmed"] = True
        evidence["load_in_confirmed"] = "arrival/load-in mentioned"

    if _has(r"\b(payment|payout|paid|paying|invoice|deposit|ach|venmo|paypal|check|cash|w-?9|net\s*\d+|honorarium)\b", inbound_text):
        inferred["payment_confirmed"] = True
        evidence["payment_confirmed"] = "payment terms mentioned"

    promo_sent = _has(
        r"\b(attached|sent|sending|sharing|shared|included|here(?:'s| is)|link(?:ed)?|uploaded)\b.{0,80}\b(epk|reel|press kit|media kit|promo|assets|flyer|poster|headshot|bio|logo)\b"
        r"|\b(epk|reel|press kit|media kit|promo|assets|flyer|poster|headshot|bio|logo)\b.{0,80}\b(attached|sent|sending|sharing|shared|included|here(?:'s| is)|link(?:ed)?|uploaded)\b",
        outbound_text,
    )
    if promo_sent:
        inferred["promo_assets_sent"] = True
        evidence["promo_assets_sent"] = "promo materials sent"

    contract_sent = _has(
        r"\b(attached|sent|sending|sharing|shared|included|here(?:'s| is)|link(?:ed)?|uploaded)\b.{0,80}\b(contract|invoice|agreement|w-?9)\b"
        r"|\b(contract|invoice|agreement|w-?9)\b.{0,80}\b(attached|sent|sending|sharing|shared|included|here(?:'s| is)|link(?:ed)?|uploaded)\b",
        outbound_text,
    )
    if contract_sent:
        inferred["contract_invoice_sent"] = True
        evidence["contract_invoice_sent"] = "contract/invoice sent"

    for key, value in inferred.items():
        if value and key in checklist:
            checklist[key] = True

    core_ready = all(checklist.get(key) for key in ("date_confirmed", "rate_confirmed", "contact_confirmed"))
    show_ready = all(checklist.get(key) for key in ("date_confirmed", "rate_confirmed", "contact_confirmed", "set_length_confirmed", "load_in_confirmed", "payment_confirmed"))
    if booking.conversation_stage in {"secured", "confirmed"} and core_ready:
        booking.conversation_stage = "logistics_pending"
    if booking.conversation_stage in {"secured", "confirmed", "logistics_pending", "logistics"} and show_ready:
        booking.conversation_stage = "show_scheduled"

    booking.logistics_checklist = checklist_json(checklist)

    after = {
        "checklist": checklist,
        "show_date": booking.show_date,
        "agreed_rate": booking.agreed_rate,
        "stage": booking.conversation_stage,
    }
    changed = before != after
    if not changed:
        return False, evidence

    booking.updated_at = datetime.utcnow()
    summary = _summarize_changes(evidence)
    db.add(models.AgentEvent(
        agent_id="agent4",
        event_type="logistics_auto_update",
        message=f"Auto-filled Pipeline logistics for {booking.venue_name}: {summary or 'thread context'}",
        entertainer_id=booking.entertainer_id,
        target_id=booking.target_id,
        conclusion=json.dumps(evidence),
    ))
    db.commit()
    db.refresh(booking)
    return True, evidence


def apply_auto_logistics_to_bookings(db: Session, bookings: list[models.Booking]) -> list[models.Booking]:
    for booking in bookings:
        apply_auto_logistics_to_booking(db, booking)
    return bookings
