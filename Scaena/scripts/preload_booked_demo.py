"""
Preload three booked demo interactions without clearing local app state.

Run from the Scaena directory:
    python scripts/preload_booked_demo.py
"""
import json
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from backend.database import init_db, SessionLocal
from backend import models
from backend.services.booking_pipeline import checklist_json
from backend.services.pitch_generation import remove_long_dashes


def _slug(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-")


def _set_attrs(obj, values: dict):
    for key, value in values.items():
        setattr(obj, key, value)
    return obj


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _get_or_create_by_id(db, model, object_id: str, values: dict):
    obj = db.query(model).filter(model.id == object_id).first()
    if obj is None:
        obj = model(id=object_id)
        db.add(obj)
        db.flush()
    return _set_attrs(obj, values)


def _active_demo_entertainer(db):
    joe = (
        db.query(models.Entertainer)
        .filter(models.Entertainer.name == "Joe Bruin", models.Entertainer.is_active == True)
        .order_by(models.Entertainer.created_at.desc())
        .first()
    )
    if joe:
        return joe

    active = (
        db.query(models.Entertainer)
        .filter(models.Entertainer.is_active == True)
        .order_by(models.Entertainer.created_at.desc())
        .first()
    )
    if active:
        return active

    joe = models.Entertainer(
        id="ent-joe-bruin",
        name="Joe Bruin",
        type="rapper",
        genre="Hip-hop / Rap",
        location="Los Angeles, CA",
        experience_years=2,
        social_followers=4800,
        highlights=(
            "Demo profile: targeting college campuses, music festivals, music shows, "
            "and bars at $300-400 per performance."
        ),
        links=json.dumps({
            "instagram": "@joebruin_rap",
            "tiktok": "@joebruinofficial",
            "youtube": "JoeBruinRap",
        }),
        current_rate=350,
        outreach_mode="auto_pitch",
        is_active=True,
    )
    db.add(joe)
    db.flush()
    return joe


def _demo_deals(artist_name: str, recipient_email: str):
    now = _utcnow()
    return [
        {
            "venue_name": "UCLA Campus Events",
            "contact_name": "Campus Events Team",
            "venue_type": "College",
            "typical_pay": "$350-600/show",
            "fit_score": 0.96,
            "rate": 400,
            "show_date": (now + timedelta(days=14)).strftime("%Y-%m-%d"),
            "stage": "show_scheduled",
            "subject": f"Confirmed campus set for {artist_name}",
            "initial": (
                f"Hi UCLA Campus Events Team,\n\n"
                f"We represent {artist_name}, a Los Angeles rapper building a strong college crowd. "
                f"He can bring a high-energy 30-minute set that fits a campus night, student showcase, "
                f"or opener slot. His normal range is $300-400, and we can make $400 work for a full campus set.\n\n"
                f"Sincerely,\n{artist_name}'s Team"
            ),
            "reply": (
                f"Hi {artist_name}'s Team, this sounds like a strong fit. We can confirm $400 for a "
                f"30-minute set at our campus showcase. The date works on our side."
            ),
            "confirmation": (
                f"Hi UCLA Campus Events Team,\n\n"
                f"Perfect, confirming {artist_name} for the campus showcase at $400. We have the date, "
                f"set length, load-in, promo assets, and payment details marked confirmed.\n\n"
                f"Sincerely,\n{artist_name}'s Team"
            ),
            "booking_note": "All core logistics are confirmed. Keep monitoring until show day.",
            "checklist": {
                "date_confirmed": True,
                "rate_confirmed": True,
                "contact_confirmed": True,
                "set_length_confirmed": True,
                "load_in_confirmed": True,
                "payment_confirmed": True,
                "promo_assets_sent": True,
                "contract_invoice_sent": True,
            },
        },
        {
            "venue_name": "The Roxy Theatre",
            "contact_name": "Talent Buying Team",
            "venue_type": "Music Venue",
            "typical_pay": "$300-500/show",
            "fit_score": 0.92,
            "rate": 350,
            "show_date": (now + timedelta(days=18)).strftime("%Y-%m-%d"),
            "stage": "logistics_pending",
            "subject": f"{artist_name} support slot confirmation",
            "initial": (
                f"Hi The Roxy Talent Team,\n\n"
                f"We represent {artist_name}, a hip-hop artist in LA looking for rooms that match a young, "
                f"music-first crowd. A support slot at The Roxy makes sense for his current audience and "
                f"keeps the economics simple at $350.\n\n"
                f"Sincerely,\n{artist_name}'s Team"
            ),
            "reply": (
                f"Hi {artist_name}'s Team, we like the fit for an early support slot. We can do $350. "
                f"Please send over a short EPK and confirm whether a 25-minute set works."
            ),
            "confirmation": (
                f"Hi The Roxy Talent Team,\n\n"
                f"Thanks, $350 and a 25-minute support set works for {artist_name}. We will send the EPK "
                f"and promo assets today, then wait on final load-in details from your side.\n\n"
                f"Sincerely,\n{artist_name}'s Team"
            ),
            "booking_note": "Rate and set length are confirmed. Load-in and final promo handoff still need tracking.",
            "checklist": {
                "date_confirmed": True,
                "rate_confirmed": True,
                "contact_confirmed": True,
                "set_length_confirmed": True,
                "payment_confirmed": True,
            },
        },
        {
            "venue_name": "Bardot Hollywood",
            "contact_name": "Nightlife Booking Team",
            "venue_type": "Bar",
            "typical_pay": "$250-400/show",
            "fit_score": 0.88,
            "rate": 325,
            "show_date": (now + timedelta(days=21)).strftime("%Y-%m-%d"),
            "stage": "secured",
            "subject": f"{artist_name} booked for Bardot Hollywood",
            "initial": (
                f"Hi Bardot Booking Team,\n\n"
                f"We represent {artist_name}. He is looking for intimate LA rooms and bar nights where "
                f"a sharp hip-hop set can turn casual traffic into fans. His normal rate is $300-400, "
                f"and we can work with $325 for the right night.\n\n"
                f"Sincerely,\n{artist_name}'s Team"
            ),
            "reply": (
                f"Hi {artist_name}'s Team, $325 works for us. We can put him on the bill for our upcoming "
                f"hip-hop night. Please confirm the best contact for day-of coordination."
            ),
            "confirmation": (
                f"Hi Bardot Booking Team,\n\n"
                f"Great, confirming $325 for {artist_name}. The best day-of contact will be his team email, "
                f"and we will send promo materials once the flyer is ready.\n\n"
                f"Sincerely,\n{artist_name}'s Team"
            ),
            "booking_note": "Deal is secured. Follow up on flyer timing, load-in, and payout method.",
            "checklist": {
                "date_confirmed": True,
                "rate_confirmed": True,
                "contact_confirmed": True,
            },
        },
    ]


def preload():
    init_db()
    db = SessionLocal()
    try:
        artist = _active_demo_entertainer(db)
        artist_name = artist.name or "Joe Bruin"
        recipient_email = os.getenv("GMAIL_TEST_RECIPIENT") or "demo-recipient@example.com"
        now = _utcnow()
        created = []

        for idx, deal in enumerate(_demo_deals(artist_name, recipient_email)):
            slug = _slug(deal["venue_name"])
            base_time = now - timedelta(days=7 - idx)

            venue = (
                db.query(models.Venue)
                .filter(models.Venue.entertainer_id == artist.id, models.Venue.name == deal["venue_name"])
                .first()
            )
            if venue is None:
                venue = models.Venue(entertainer_id=artist.id, name=deal["venue_name"])
                db.add(venue)
                db.flush()
            _set_attrs(venue, {
                "contact_name": deal["contact_name"],
                "contact_email": recipient_email,
                "venue_type": deal["venue_type"],
                "typical_pay": deal["typical_pay"],
                "fit_score": deal["fit_score"],
                "contact_approach": "Demo booked interaction seeded for hackathon walkthrough.",
                "why_fits": f"{deal['venue_name']} is a strong fit for {artist_name}'s live hip-hop audience.",
                "specific_examples": json.dumps([deal["venue_name"], "Booked demo interaction"]),
            })

            pitch = (
                db.query(models.Pitch)
                .filter(models.Pitch.entertainer_id == artist.id, models.Pitch.venue_name == deal["venue_name"])
                .order_by(models.Pitch.created_at.desc())
                .first()
            )
            if pitch is None:
                pitch = models.Pitch(
                    id=f"demo-booked-pitch-{slug}",
                    entertainer_id=artist.id,
                    venue_name=deal["venue_name"],
                )
                db.add(pitch)
                db.flush()
            _set_attrs(pitch, {
                "venue_id": venue.id,
                "batch_id": "hackathon-booked-demo",
                "entertainer_type": artist.type or "rapper",
                "recipient_email": recipient_email,
                "venue_contact_approach": "Demo booked interaction",
                "pitch_subject": remove_long_dashes(deal["subject"]),
                "pitch_body": remove_long_dashes(deal["initial"]),
                "proposed_rate": deal["rate"],
                "status": "booked",
                "response_type": "accepted",
                "negotiated_price": deal["rate"],
                "gmail_message_id": f"demo-gmail-{slug}-initial",
                "gmail_thread_id": f"demo-thread-{slug}",
                "sent_at": base_time,
                "created_at": base_time - timedelta(hours=2),
            })

            conv = db.query(models.Conversation).filter(models.Conversation.pitch_id == pitch.id).first()
            if conv is None:
                conv = models.Conversation(
                    id=f"demo-conv-{slug}",
                    entertainer_id=artist.id,
                    pitch_id=pitch.id,
                    venue_name=deal["venue_name"],
                )
                db.add(conv)
                db.flush()
            _set_attrs(conv, {
                "entertainer_id": artist.id,
                "pitch_id": pitch.id,
                "venue_name": deal["venue_name"],
                "interest_level": "high",
                "signals": json.dumps(["Booked", "Rate accepted", "Date in progress"]),
                "what_worked": "Specific venue fit, clear rate, and concise team-based tone.",
                "what_to_do_next": "Track logistics, then resolve performance after show day.",
                "conversion_likelihood": 9.4,
                "updated_at": now,
            })

            messages = [
                ("initial", "outbound", "initial_pitch", deal["subject"], deal["initial"], base_time),
                ("reply", "inbound", "reply", None, deal["reply"], base_time + timedelta(days=1, hours=2)),
                ("confirm", "outbound", "gmail_final_thanks_sent", f"Confirmed: {deal['venue_name']}", deal["confirmation"], base_time + timedelta(days=1, hours=3)),
            ]
            for msg_key, direction, message_type, subject, body, created_at in messages:
                _get_or_create_by_id(db, models.ConversationMessage, f"demo-msg-{slug}-{msg_key}", {
                    "conversation_id": conv.id,
                    "direction": direction,
                    "message_type": message_type,
                    "subject": remove_long_dashes(subject),
                    "body": remove_long_dashes(body),
                    "sentiment": "positive" if direction == "inbound" else None,
                    "gmail_message_id": f"demo-gmail-{slug}-{msg_key}",
                    "gmail_thread_id": f"demo-thread-{slug}",
                    "from_email": recipient_email if direction == "inbound" else None,
                    "created_at": created_at,
                })

            booking = (
                db.query(models.Booking)
                .filter(models.Booking.entertainer_id == artist.id, models.Booking.venue_name == deal["venue_name"])
                .first()
            )
            if booking is None:
                booking = models.Booking(id=f"demo-booking-{slug}")
                db.add(booking)
                db.flush()
            _set_attrs(booking, {
                "entertainer_id": artist.id,
                "pitch_id": pitch.id,
                "target_id": conv.id,
                "venue_name": deal["venue_name"],
                "agreed_rate": deal["rate"],
                "show_date": deal["show_date"],
                "conversation_stage": deal["stage"],
                "logistics_checklist": checklist_json(deal["checklist"]),
                "original_pitch_id": pitch.id,
                "show_summary": deal["booking_note"],
                "post_show_notes": None,
                "crowd_size": None,
                "audience_reaction": None,
                "payout_received": False,
                "venue_satisfaction": None,
                "rebook_recommended": True,
                "next_reminder_at": now + timedelta(days=3 + idx),
                "performance_completed_at": None,
                "rebooking_sent": False,
                "updated_at": now,
            })

            _get_or_create_by_id(db, models.BookingMessage, f"demo-booking-msg-{slug}", {
                "booking_id": booking.id,
                "entertainer_id": artist.id,
                "target_id": conv.id,
                "stage": deal["stage"],
                "subject": f"Pipeline note: {deal['venue_name']}",
                "body": remove_long_dashes(deal["booking_note"]),
                "status": "sent",
                "sent_at": base_time + timedelta(days=1, hours=4),
                "created_at": base_time + timedelta(days=1, hours=4),
            })

            _get_or_create_by_id(db, models.AgentEvent, f"demo-agent-event-{slug}", {
                "agent_id": "agent2",
                "event_type": "booked",
                "message": f"{deal['venue_name']} reached booked stage at ${deal['rate']}.",
                "entertainer_id": artist.id,
                "target_id": conv.id,
                "conclusion": "Booked demo interaction preloaded for hackathon.",
                "extra": json.dumps({"venue_name": deal["venue_name"], "rate": deal["rate"]}),
                "created_at": base_time + timedelta(days=1, hours=5),
            })
            created.append(deal["venue_name"])

        db.commit()
        print(f"Preloaded {len(created)} booked demo interactions for {artist_name}:")
        for venue_name in created:
            print(f"  - {venue_name}")
    finally:
        db.close()


if __name__ == "__main__":
    preload()
