"""
Seed script: creates a demo entertainer with 3 weeks of pipeline history.
Run from scaena/ directory: python seed.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from backend.database import init_db, SessionLocal
from backend import models
from backend.services.pitch_generation import generate_pitch_for_venue
from backend.services.booking_pipeline import checklist_json
import json
from datetime import datetime, timedelta

def seed():
    init_db()
    db = SessionLocal()

    # Clear existing data
    for cls in [models.AgentEvent, models.BookingMessage, models.Booking, models.Reengagement,
                models.FollowUpResult, models.FollowUp, models.OutreachBatch, models.ConversationMessage,
                models.Conversation, models.Pitch, models.LearningInsight, models.Venue, models.Entertainer]:
        db.query(cls).delete()
    db.commit()

    # Entertainer: Joe Bruin (rapper)
    joe = models.Entertainer(
        id="ent-joe-bruin",
        name="Joe Bruin",
        type="rapper",
        genre="Hip-hop / Rap",
        location="Los Angeles, CA",
        experience_years=2,
        social_followers=4800,
        highlights="Goal: earn $10k+, reach 1000+ people. Targeting college campuses, music festivals, music shows, and bars.",
        links=json.dumps({"instagram": "@joebruin_rap", "tiktok": "@joebruinofficial", "youtube": "JoeBruinRap"}),
        current_rate=350.0,
        outreach_mode="auto_pitch",
    )
    db.add(joe)

    # Venues
    venue_data = [
        ("UCLA Campus Events", "Campus Booking Team", "ucla-campus-events@example.com", "College", "$350-600/show", 0.95, "Email student activities board", "Joe's college-rap style is a perfect match for UCLA's 45,000-student campus crowd and high-energy event culture."),
        ("USC Spring Concert", "Concerts Committee", "usc-spring-concert@example.com", "College", "$300-550/show", 0.92, "Contact student programming board", "USC's Greek life and campus events scene drives huge turnout for emerging hip-hop acts with strong social presence."),
        ("The Roxy Theatre", "Talent Buyer", "roxy-booking@example.com", "Music Venue", "$300-500/show", 0.90, "Submit EPK to booking manager", "The Roxy's Sunset Strip stage hosts LA's best emerging acts, ideal for Joe's genre and crowd demographic."),
        ("UCSD Sun God Festival", "Festival Programming", "ucsd-sungod@example.com", "Festival", "$400-700/show", 0.88, "Submit via festival application portal", "Sun God draws 20,000+ students per year, massive exposure aligned with Joe's 1000+ people goal."),
        ("Bardot Hollywood", "Nightlife Booking", "bardot-booking@example.com", "Bar", "$250-400/show", 0.85, "DM booking manager on Instagram", "Bardot's hip-hop nights pull a college-age crowd that matches Joe's fanbase, great for building local presence."),
        ("The Troubadour", "Talent Buyer", "troubadour-booking@example.com", "Music Venue", "$350-600/show", 0.87, "Email booking desk", "West Hollywood institution with loyal music fans. A Troubadour credit adds real industry credibility."),
        ("Harvard & Stone", "Venue Manager", "harvard-stone-booking@example.com", "Bar", "$200-350/show", 0.78, "Contact owner directly via email", "Rock/hip-hop crossover bar in East Hollywood with built-in late-night crowd, easy to fill for new artists."),
        ("UC Berkeley Cal Performances", "Student Union Programming", "cal-performances@example.com", "College", "$350-600/show", 0.85, "Reach out to student union programming", "Berkeley's progressive student culture actively books emerging independent hip-hop, strong fit for Joe."),
        ("The Echo / Echoplex", "Local Booking Desk", "echo-booking@example.com", "Music Venue", "$250-450/show", 0.83, "Submit to booking via website form", "Echo Park venue known for launching LA artists, strong community vibe and repeat-audience loyalty."),
        ("Coachella Valley Music Festival", "Emerging Stage Talent", "coachella-emerging@example.com", "Festival", "$500-1000/show", 0.80, "Submit press kit to talent buyer", "Coachella's emerging stage is an achievable target for acts with regional buzz and growing social numbers."),
    ]
    venues = []
    for name, contact_name, contact_email, vtype, pay, score, approach, why in venue_data:
        v = models.Venue(
            entertainer_id=joe.id,
            name=name,
            contact_name=contact_name,
            contact_email=contact_email,
            venue_type=vtype,
            typical_pay=pay,
            fit_score=score,
            contact_approach=approach,
            why_fits=why,
            specific_examples=json.dumps([name]),
        )
        db.add(v)
        venues.append(v)
    db.commit()

    # Week 1 pitches, sent 3 weeks ago
    week1_scenarios = [
        ("UCLA Campus Events", "booked", "accepted", 400.0),
        ("USC Spring Concert", "responded", "negotiating", None),
        ("The Roxy Theatre", "booked", "accepted", 350.0),
        ("UCSD Sun God Festival", "sent", None, None),
        ("Bardot Hollywood", "booked", "accepted", 325.0),
        ("The Troubadour", "sent", None, None),
        ("Harvard & Stone", "sent", None, None),
        ("UC Berkeley Cal Performances", "responded", "rejected", None),
        ("The Echo / Echoplex", "responded", "maybe", None),
        ("Coachella Valley Music Festival", "sent", None, None),
    ]

    pitches_w1 = []
    batch_id_1 = "batch-week1"
    original_asi_key = os.environ.get("ASI1_API_KEY")
    os.environ["ASI1_API_KEY"] = "placeholder"
    entertainer_payload = {
        "name": joe.name,
        "type": joe.type,
        "genre": joe.genre,
        "location": joe.location,
        "experience_years": joe.experience_years,
        "social_followers": joe.social_followers,
        "highlights": joe.highlights,
        "current_rate": joe.current_rate,
    }
    generated_pitches = {}
    for venue in venues:
        generated_pitches[venue.name] = generate_pitch_for_venue(entertainer_payload, {
            "name": venue.name,
            "venue_type": venue.venue_type,
            "contact_approach": venue.contact_approach,
            "why_fits": venue.why_fits,
            "specific_examples": venue.specific_examples,
        }, joe.current_rate)
    if original_asi_key is None:
        os.environ.pop("ASI1_API_KEY", None)
    else:
        os.environ["ASI1_API_KEY"] = original_asi_key
    for i, (venue_name, status, response_type, neg_price) in enumerate(week1_scenarios):
        generated_pitch = generated_pitches.get(venue_name, {
            "subject": f"Performance booking: Joe Bruin for {venue_name}",
            "body": f"Hi,\n\nWe represent Joe Bruin, a rapper from LA looking to book a show at {venue_name}.\n\nRate: $350/show.\n\nSincerely,\nJoe Bruin's Team",
        })
        p = models.Pitch(
            entertainer_id=joe.id,
            batch_id=batch_id_1,
            venue_name=venue_name,
            entertainer_type="rapper",
            recipient_email=next((email for name, _, email, *_ in venue_data if name == venue_name), None),
            pitch_subject=generated_pitch["subject"],
            pitch_body=generated_pitch["body"],
            proposed_rate=350.0,
            status=status,
            response_type=response_type,
            negotiated_price=neg_price,
            sent_at=datetime.utcnow() - timedelta(days=21),
            created_at=datetime.utcnow() - timedelta(days=22),
        )
        db.add(p)
        pitches_w1.append(p)

    db.commit()

    # Conversations + messages for week 1
    for i, (pitch, (venue_name, status, response_type, _)) in enumerate(zip(pitches_w1, week1_scenarios)):
        conv = models.Conversation(
            entertainer_id=joe.id,
            pitch_id=pitch.id,
            venue_name=venue_name,
            interest_level="high" if response_type == "accepted" else "medium" if response_type in ("negotiating", "interested") else "low" if response_type == "rejected" else None,
            what_worked="Direct, personal tone with specific crowd and social data",
            what_to_do_next="Send performance reel and propose 2 specific dates" if response_type in ("interested", "negotiating") else None,
            conversion_likelihood=8.5 if response_type == "accepted" else 5.5 if response_type == "negotiating" else 3.0 if response_type == "rejected" else None,
            signals=json.dumps(["Reply received", "Positive engagement" if response_type in ("accepted", "interested") else "Budget objection" if response_type == "rejected" else "Standard inquiry"]),
        )
        db.add(conv)
        db.flush()

        # Initial pitch message
        db.add(models.ConversationMessage(
            conversation_id=conv.id,
            direction="outbound",
            message_type="initial_pitch",
            subject=pitch.pitch_subject,
            body=pitch.pitch_body,
            created_at=datetime.utcnow() - timedelta(days=21),
        ))

        # Reply messages for responded pitches
        replies = {
            "accepted": "Joe! Love the energy, we'd love to have you. Our rate for emerging acts is $400/show. Does that work for a date in May?",
            "negotiating": "Hey Joe, thanks for reaching out. We're interested but a bit tight on budget. Could you work with $280? We do good crowd numbers.",
            "interested": "Hey! This looks great. Can you send your performance reel and a few dates you're free? We're booking out the next 6 weeks.",
            "rejected": "Thanks for reaching out, Joe. We're fully booked through the semester. Best of luck with the music!",
            "maybe": "Hi Joe, nice pitch. We're locking in the fall lineup in a couple months. Follow up then and we'll see what we can do.",
        }
        if response_type in replies:
            db.add(models.ConversationMessage(
                conversation_id=conv.id,
                direction="inbound",
                message_type="reply",
                body=replies[response_type],
                sentiment="positive" if response_type in ("accepted", "interested") else "negative" if response_type == "rejected" else "neutral",
                created_at=datetime.utcnow() - timedelta(days=18),
            ))

    db.commit()

    # Booked demo interactions for Pipeline
    ucla_pitch = pitches_w1[0]
    ucla_conv = db.query(models.Conversation).filter(models.Conversation.pitch_id == ucla_pitch.id).first()
    booking = models.Booking(
        entertainer_id=joe.id,
        pitch_id=ucla_pitch.id,
        target_id=ucla_conv.id if ucla_conv else ucla_pitch.id,
        venue_name="UCLA Campus Events",
        agreed_rate=400.0,
        show_date=(datetime.utcnow() + timedelta(days=14)).strftime("%Y-%m-%d"),
        conversation_stage="show_scheduled",
        logistics_checklist=checklist_json({
            "date_confirmed": True,
            "rate_confirmed": True,
            "contact_confirmed": True,
            "set_length_confirmed": True,
            "load_in_confirmed": True,
            "payment_confirmed": True,
            "promo_assets_sent": True,
            "contract_invoice_sent": True,
        }),
        original_pitch_id=ucla_pitch.id,
    )
    db.add(booking)

    roxy_pitch = pitches_w1[2]
    roxy_conv = db.query(models.Conversation).filter(models.Conversation.pitch_id == roxy_pitch.id).first()
    booking2 = models.Booking(
        entertainer_id=joe.id,
        pitch_id=roxy_pitch.id,
        target_id=roxy_conv.id if roxy_conv else roxy_pitch.id,
        venue_name="The Roxy Theatre",
        agreed_rate=350.0,
        show_date=(datetime.utcnow() + timedelta(days=18)).strftime("%Y-%m-%d"),
        conversation_stage="logistics_pending",
        logistics_checklist=checklist_json({
            "date_confirmed": True,
            "rate_confirmed": True,
            "contact_confirmed": True,
            "set_length_confirmed": True,
            "payment_confirmed": True,
        }),
        original_pitch_id=roxy_pitch.id,
    )
    db.add(booking2)

    bardot_pitch = pitches_w1[4]
    bardot_conv = db.query(models.Conversation).filter(models.Conversation.pitch_id == bardot_pitch.id).first()
    booking3 = models.Booking(
        entertainer_id=joe.id,
        pitch_id=bardot_pitch.id,
        target_id=bardot_conv.id if bardot_conv else bardot_pitch.id,
        venue_name="Bardot Hollywood",
        agreed_rate=325.0,
        show_date=(datetime.utcnow() + timedelta(days=21)).strftime("%Y-%m-%d"),
        conversation_stage="secured",
        logistics_checklist=checklist_json({
            "date_confirmed": True,
            "rate_confirmed": True,
            "contact_confirmed": True,
        }),
        original_pitch_id=bardot_pitch.id,
    )
    db.add(booking3)
    db.commit()

    # Analytics snapshot
    db.add(models.LearningInsight(
        entertainer_id=joe.id,
        round_number=1,
        best_venue_types=json.dumps(["College", "Music Venue"]),
        avoid_segments=json.dumps(["Comedy Clubs", "Private events under $300"]),
        best_pitch_angle="Campus-energy, social draw, crowd-building",
        optimal_price=375.0,
        insights_narrative="College venues are converting at 60%+ response rate with a direct, personal pitch tone. Music venues on Sunset/Echo Park are strong for credibility building, and bars are reliable for consistent income inside Joe's $300-400 range.",
    ))

    # Agent events (simulated history)
    events = [
        ("agent1", "complete", "Found 10 venues for Joe Bruin. Rate: $350/show. Sending to Agent 2."),
        ("agent2", "complete", "10 pitches generated (mode: auto_pitch)"),
        ("agent3", "insight", "Direct, personal tone with social data resonated with college bookers"),
        ("agent4", "followup_ready", "Follow-up #1 ready for USC Spring Concert"),
        ("agent3", "complete", "Round 1 insights ready for approval."),
    ]
    for agent_id, event_type, message in events:
        db.add(models.AgentEvent(
            agent_id=agent_id,
            event_type=event_type,
            message=message,
            entertainer_id=joe.id,
            created_at=datetime.utcnow() - timedelta(hours=len(events) - events.index((agent_id, event_type, message))),
        ))

    db.commit()
    entertainer_id = joe.id
    db.close()

    print("✓ Seeded Joe Bruin (rapper) with 3-week pipeline")
    print(f"  Entertainer ID: {entertainer_id}")
    print(f"  10 venues, 10 week-1 pitches")
    print(f"  3 bookings (UCLA Campus Events $400, The Roxy Theatre $350, Bardot Hollywood $325)")
    print(f"  Learning insights round 1")

if __name__ == "__main__":
    seed()
