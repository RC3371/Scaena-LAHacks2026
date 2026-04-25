"""
Seed script: creates a realistic demo dataset showing 3 weeks of compounding improvement.
Run: python seed_data.py
"""

import sqlite3
import json
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))
from database import init_db, DB_PATH

init_db()

PROSPECTS = [
    {"name": "The Comedy Store", "type": "Comedy Club", "location": "Los Angeles, CA", "contact_name": "Mike Thompson", "contact_email": "booking@thecomedystore.com", "typical_pay_min": 200, "typical_pay_max": 400},
    {"name": "Laugh Factory Hollywood", "type": "Comedy Club", "location": "Los Angeles, CA", "contact_name": "Sarah Chen", "contact_email": "talent@laughfactory.com", "typical_pay_min": 200, "typical_pay_max": 500},
    {"name": "Improv Comedy Club", "type": "Comedy Club", "location": "Hollywood, CA", "contact_name": "Dave Rodriguez", "contact_email": "shows@improv.com", "typical_pay_min": 150, "typical_pay_max": 350},
    {"name": "Flappers Comedy Club", "type": "Comedy Club", "location": "Burbank, CA", "contact_name": "Lisa Park", "contact_email": "booking@flapperscomedy.com", "typical_pay_min": 100, "typical_pay_max": 250},
    {"name": "Ice House Comedy Club", "type": "Comedy Club", "location": "Pasadena, CA", "contact_name": "Tom Wilson", "contact_email": "tom@icehousecomedy.com", "typical_pay_min": 150, "typical_pay_max": 300},
    {"name": "Ha Ha Comedy Club", "type": "Comedy Club", "location": "North Hollywood, CA", "contact_name": "Maria Santos", "contact_email": "maria@hahacomedy.com", "typical_pay_min": 100, "typical_pay_max": 250},
    {"name": "Westside Comedy Theater", "type": "Comedy Club", "location": "Santa Monica, CA", "contact_name": "James Lee", "contact_email": "bookings@westsidecomedy.com", "typical_pay_min": 100, "typical_pay_max": 200},
    {"name": "Comedy & Magic Club", "type": "Comedy Club", "location": "Hermosa Beach, CA", "contact_name": "Karen White", "contact_email": "karen@comedymagicclub.com", "typical_pay_min": 200, "typical_pay_max": 400},
    {"name": "Acme Comedy Theatre", "type": "Comedy Club", "location": "Los Angeles, CA", "contact_name": "Frank Nguyen", "contact_email": "talent@acmecomedy.com", "typical_pay_min": 150, "typical_pay_max": 300},
    {"name": "Second City Los Angeles", "type": "Comedy Club", "location": "West Hollywood, CA", "contact_name": "Amy Johnson", "contact_email": "amy@secondcity.com", "typical_pay_min": 200, "typical_pay_max": 450},
    {"name": "Google LA All-Hands Event", "type": "Corporate Event", "location": "Culver City, CA", "contact_name": "Rachel Kim", "contact_email": "rachel.kim@google.com", "typical_pay_min": 2000, "typical_pay_max": 5000},
    {"name": "Spotify Holiday Party", "type": "Corporate Event", "location": "Santa Monica, CA", "contact_name": "Eric Davis", "contact_email": "events@spotify.com", "typical_pay_min": 2500, "typical_pay_max": 6000},
    {"name": "Warner Bros Entertainment Night", "type": "Corporate Event", "location": "Burbank, CA", "contact_name": "Linda Martinez", "contact_email": "entertainment@warnerbros.com", "typical_pay_min": 3000, "typical_pay_max": 8000},
    {"name": "USC Trojan Events", "type": "College Venue", "location": "Los Angeles, CA", "contact_name": "Chris Brown", "contact_email": "usc.events@usc.edu", "typical_pay_min": 500, "typical_pay_max": 1500},
    {"name": "UCLA Student Union Events", "type": "College Venue", "location": "Westwood, CA", "contact_name": "Olivia Turner", "contact_email": "events@ucla.edu", "typical_pay_min": 500, "typical_pay_max": 1500},
    {"name": "LMU Campus Events", "type": "College Venue", "location": "Playa Vista, CA", "contact_name": "Daniel Cho", "contact_email": "events@lmu.edu", "typical_pay_min": 300, "typical_pay_max": 1000},
    {"name": "Just for Laughs LA", "type": "Comedy Festival", "location": "Los Angeles, CA", "contact_name": "Sophie Martin", "contact_email": "submissions@jfl.com", "typical_pay_min": 500, "typical_pay_max": 2000},
    {"name": "SF Sketchfest", "type": "Comedy Festival", "location": "San Francisco, CA", "contact_name": "Paul Anderson", "contact_email": "talent@sketchfest.com", "typical_pay_min": 400, "typical_pay_max": 1500},
    {"name": "Bridgetown Comedy Festival", "type": "Comedy Festival", "location": "Portland, OR", "contact_name": "Emma Clark", "contact_email": "em@bridgetowncomedy.com", "typical_pay_min": 300, "typical_pay_max": 1000},
    {"name": "Cobb's Comedy Club SF", "type": "Comedy Club", "location": "San Francisco, CA", "contact_name": "Tony Ross", "contact_email": "booking@cobbscomedy.com", "typical_pay_min": 200, "typical_pay_max": 400},
    {"name": "Punchline Comedy Club SF", "type": "Comedy Club", "location": "San Francisco, CA", "contact_name": "Jessica Wu", "contact_email": "jess@punchlinecomedy.com", "typical_pay_min": 150, "typical_pay_max": 350},
    {"name": "Side Splitters Comedy Club", "type": "Comedy Club", "location": "Tampa, FL", "contact_name": "Mark Collins", "contact_email": "mark@sidesplitterscomedy.com", "typical_pay_min": 150, "typical_pay_max": 300},
    {"name": "Zanies Nashville", "type": "Comedy Club", "location": "Nashville, TN", "contact_name": "Carol Hayes", "contact_email": "carol@zanies.com", "typical_pay_min": 150, "typical_pay_max": 350},
    {"name": "The Stand NYC", "type": "Comedy Club", "location": "New York, NY", "contact_name": "Alex Rivera", "contact_email": "alex@thestandnyc.com", "typical_pay_min": 200, "typical_pay_max": 500},
    {"name": "Carolines on Broadway", "type": "Comedy Club", "location": "New York, NY", "contact_name": "Natalie Fox", "contact_email": "booking@carolines.com", "typical_pay_min": 300, "typical_pay_max": 700},
    {"name": "Netflix Is A Joke Submissions", "type": "Comedy Festival", "location": "Los Angeles, CA", "contact_name": "Steve Harper", "contact_email": "talent@netflixisajoke.com", "typical_pay_min": 1000, "typical_pay_max": 5000},
    {"name": "Paramount Pictures Event", "type": "Corporate Event", "location": "Hollywood, CA", "contact_name": "Diana Reed", "contact_email": "events@paramount.com", "typical_pay_min": 2000, "typical_pay_max": 6000},
    {"name": "Cal State LA Events", "type": "College Venue", "location": "Los Angeles, CA", "contact_name": "Brian Patel", "contact_email": "events@calstatela.edu", "typical_pay_min": 300, "typical_pay_max": 800},
    {"name": "The Wiltern Late Night", "type": "Concert Hall", "location": "Los Angeles, CA", "contact_name": "Stephanie Long", "contact_email": "steph@thewiltern.com", "typical_pay_min": 500, "typical_pay_max": 1500},
    {"name": "Comedy Central Showcase", "type": "Comedy Festival", "location": "Los Angeles, CA", "contact_name": "Ryan Simmons", "contact_email": "talent@comedycentral.com", "typical_pay_min": 1000, "typical_pay_max": 4000},
]

RESPONSE_SCENARIOS = [
    (0, "interested", "Hey! We'd love to have you. Let's talk dates for next month."),
    (1, "booked", "We're in! Can you do Saturday the 15th at 9pm? $350 works for us."),
    (2, "negotiating", "Interested but we can only do $250 for new acts. Any flexibility?"),
    (3, "maybe", "Send over your reel and we'll consider you for Q3."),
    (4, "interested", "Great timing, we have an opening. Can you send your media kit?"),
    (5, "not_interested", "We're fully booked through summer. Try us again in fall."),
    (6, "booked", "Yes! You're booked for March 8th. $400 flat. See you then!"),
    (7, "negotiating", "Rate is a bit high for us. What's your bottom line?"),
    (9, "interested", "Love the energy. Let's get on a call this week."),
    (11, "booked", "Corporate event confirmed! $3500 for 45-minute set. Contracts coming."),
    (13, "interested", "Students would love you! Submit our online form and we'll review."),
    (16, "maybe", "Festival applications closed but keep an eye on our website for next year."),
]

def seed():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")

        conn.execute("DELETE FROM analytics_snapshots")
        conn.execute("DELETE FROM follow_ups")
        conn.execute("DELETE FROM pitch_responses")
        conn.execute("DELETE FROM pitches")
        conn.execute("DELETE FROM prospects")
        conn.execute("DELETE FROM market_research")
        conn.execute("DELETE FROM profiles")
        conn.execute("DELETE FROM sqlite_sequence")

        cursor = conn.execute(
            """INSERT INTO profiles (name, entertainer_type, genre_style, experience_years, shows_count,
               location, touring_region, rate_min, rate_max, youtube_url, instagram_url, instagram_followers, bio)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            ("Alex Rivera", "comedian", "Dark humor & storytelling", 3, 52,
             "Los Angeles, CA", "West Coast + National",
             300, 400,
             "https://youtube.com/@alexrivera_comedy",
             "https://instagram.com/alexrivera_comedy", 14200,
             "Stand-up comedian blending dark humor with personal storytelling. Known for relatable takes on modern anxiety and late-stage capitalism. Regular at LA open mics, featured in two short specials."),
        )
        profile_id = cursor.lastrowid

        market_data = {
            "market_insights": {
                "entertainer_type": "comedian",
                "experience_tier": "mid_level",
                "market_rates": {"entry_level": "$50-200/show", "mid_level": "$300-1000/show", "established": "$1500-5000/show"},
                "pricing_recommendation": "Mid-level pricing at $350-450/show based on your 14.2K Instagram followers, 52 shows, and YouTube presence",
                "recommended_rate_min": 350,
                "recommended_rate_max": 450,
                "pricing_rationale": "Your social proof (14K+ followers, active YouTube) positions you above entry-level. Comedy clubs in LA typically pay $300-500 for mid-tier acts.",
            },
            "competitive_analysis": {
                "similar_entertainers_count": 38,
                "average_market_rate": 375,
                "your_current_rate": 350,
                "positioning": "slightly below market",
                "recommendation": "You could raise to $400 without losing bookings. Your YouTube presence is a differentiator most similar comedians lack.",
            },
            "key_insights": [
                "Comedy clubs average $300-400/show — you're positioned well",
                "Corporate events pay 5-8x more — consider adding a corporate tier at $1500+",
                "College venues are high-volume bookers — budget for 10-20 shows/year",
                "14K Instagram followers is above median for your experience level",
            ],
            "action_items": [
                "Create a dedicated booking page with video clips",
                "Raise comedy club rate to $400 — you're priced below market",
                "Target USC/UCLA for college circuit — consistent bookings",
            ],
        }
        conn.execute(
            "INSERT INTO market_research (profile_id, research_data) VALUES (?, ?)",
            (profile_id, json.dumps(market_data)),
        )

        prospect_ids = []
        for p in PROSPECTS:
            c = conn.execute(
                """INSERT INTO prospects (profile_id, name, type, location, contact_email, contact_name,
                   typical_pay_min, typical_pay_max, source)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'agent1')""",
                (profile_id, p["name"], p["type"], p["location"],
                 p["contact_email"], p["contact_name"],
                 p["typical_pay_min"], p["typical_pay_max"]),
            )
            prospect_ids.append(c.lastrowid)

        week1_start = datetime.now() - timedelta(days=21)
        pitch_ids = []
        for i, pid in enumerate(prospect_ids[:20]):
            sent_at = week1_start + timedelta(hours=i * 0.5)
            c = conn.execute(
                """INSERT INTO pitches (prospect_id, profile_id, subject, body, proposed_rate, status, sent_at, created_at)
                   VALUES (?, ?, ?, ?, ?, 'sent', ?, ?)""",
                (pid, profile_id,
                 f"Booking Inquiry – Alex Rivera (Stand-Up) | {PROSPECTS[i]['name']}",
                 f"Hi {PROSPECTS[i]['contact_name']},\n\nI came across {PROSPECTS[i]['name']} and I'm a huge fan of the energy you bring to your shows. I'm Alex Rivera, a stand-up comedian known for dark humor and storytelling — I've been told my style is a natural fit for your crowd.\n\nI've performed 52+ shows over 3 years, built 14,200 Instagram followers organically, and my recent YouTube set hit 45K views. Audiences consistently say my material is sharp and genuinely funny.\n\nI'm available at $350/show and completely flexible on dates. Would love to jump on a quick call.\n\nBest,\nAlex Rivera\n@alexrivera_comedy",
                 350, sent_at.isoformat(), sent_at.isoformat()),
            )
            pitch_ids.append(c.lastrowid)

        responded_pitch_indices = [idx for idx, _, __ in RESPONSE_SCENARIOS]
        booked_prospect_ids = set()
        for idx, resp_type, resp_text in RESPONSE_SCENARIOS:
            if idx >= len(pitch_ids):
                continue
            pitch_id = pitch_ids[idx]
            prospect_id = prospect_ids[idx]
            responded_at = week1_start + timedelta(days=3, hours=idx * 2)
            conn.execute(
                """INSERT INTO pitch_responses (pitch_id, prospect_id, response_type, response_text, responded_at, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (pitch_id, prospect_id, resp_type, resp_text, responded_at.isoformat(), responded_at.isoformat()),
            )
            status_map = {"interested": "responded", "booked": "booked", "negotiating": "responded",
                         "not_interested": "declined", "maybe": "responded"}
            conn.execute("UPDATE prospects SET status = ? WHERE id = ?", (status_map.get(resp_type, "responded"), prospect_id))
            conn.execute("UPDATE pitches SET status = ? WHERE id = ?",
                        ("booked" if resp_type == "booked" else "responded", pitch_id))
            if resp_type == "booked":
                booked_prospect_ids.add(prospect_id)

        no_response_pitch_ids = [pitch_ids[i] for i in range(len(pitch_ids)) if i not in responded_pitch_indices]
        for i, pitch_id in enumerate(no_response_pitch_ids[:8]):
            pitch = dict(conn.execute("SELECT * FROM pitches WHERE id = ?", (pitch_id,)).fetchone())
            prospect_id = pitch["prospect_id"]
            sent_at = datetime.fromisoformat(pitch["sent_at"])
            for seq in [1, 2]:
                fu_sent_at = sent_at + timedelta(days=RESPONSE_SCENARIOS[0][0] if seq == 1 else 7)
                conn.execute(
                    """INSERT INTO follow_ups (pitch_id, prospect_id, profile_id, sequence_number, subject, body, scheduled_for, sent_at, status, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'sent', ?)""",
                    (pitch_id, prospect_id, profile_id, seq,
                     f"Re: Booking Inquiry – Wanted to Share My Latest Set",
                     f"Hey there,\n\nI performed a set at a sold-out show last weekend and clipped the best 3 minutes — {'thought you might enjoy it' if seq == 1 else 'audiences went wild for it'}.\n\n{'Check it: https://youtube.com/@alexrivera_comedy' if seq == 1 else 'I have openings in the next 4 weeks and would love to bring this energy to your stage.'}\n\nBest, Alex",
                     (sent_at + timedelta(days=3 if seq == 1 else 7)).isoformat(),
                     fu_sent_at.isoformat(),
                     fu_sent_at.isoformat()),
                )

        week2_start = datetime.now() - timedelta(days=10)
        for i, pid in enumerate(prospect_ids[20:]):
            sent_at = week2_start + timedelta(hours=i * 0.5)
            c = conn.execute(
                """INSERT INTO pitches (prospect_id, profile_id, subject, body, proposed_rate, status, sent_at, created_at)
                   VALUES (?, ?, ?, ?, ?, 'sent', ?, ?)""",
                (pid, profile_id,
                 f"Stand-Up Booking – Alex Rivera | Reel Inside",
                 f"Hi {PROSPECTS[20 + i]['contact_name'] if 20 + i < len(PROSPECTS) else 'there'},\n\nI noticed you recently featured storytelling-style comedy — that's exactly my lane. I'm Alex Rivera, 14.2K Instagram, 52 shows, YouTube reel: https://youtube.com/@alexrivera_comedy\n\nAvailable at $400/show. Recent audiences called my set 'the highlight of the night.'\n\nOpen to a quick call this week?\n\nAlex Rivera",
                 400, sent_at.isoformat(), sent_at.isoformat()),
            )
            new_pitch_id = c.lastrowid
            if i < 4:
                resp_types = ["interested", "booked", "negotiating", "interested"]
                resp_texts = [
                    "Love the energy! Send over your tech rider.",
                    "Yes! Confirmed for the 22nd. $400 works. See you then!",
                    "Great reel. Can you do $350?",
                    "Definitely interested. What dates work for you?",
                ]
                responded_at = week2_start + timedelta(days=2, hours=i * 3)
                conn.execute(
                    """INSERT INTO pitch_responses (pitch_id, prospect_id, response_type, response_text, responded_at)
                       VALUES (?, ?, ?, ?, ?)""",
                    (new_pitch_id, pid, resp_types[i], resp_texts[i], responded_at.isoformat()),
                )
                conn.execute("UPDATE prospects SET status = ? WHERE id = ?",
                            ({"interested": "responded", "booked": "booked", "negotiating": "responded"}.get(resp_types[i], "responded"), pid))

        for i, pid in enumerate(prospect_ids[23:26]):
            scheduled_for = datetime.now() + timedelta(days=i + 1)
            week2_pitch = dict(conn.execute(
                "SELECT * FROM pitches WHERE prospect_id = ? LIMIT 1", (pid,)
            ).fetchone() or {})
            if week2_pitch.get("id"):
                conn.execute(
                    """INSERT INTO follow_ups (pitch_id, prospect_id, profile_id, sequence_number, subject, body, scheduled_for, status)
                       VALUES (?, ?, ?, ?, ?, ?, ?, 'scheduled')""",
                    (week2_pitch["id"], pid, profile_id, 1,
                     "Re: Booking – Quick Video for You",
                     "Hey! Wanted to share a clip from my latest show. The crowd was electric. Would love to bring this to your stage.\n\nAlex",
                     scheduled_for.isoformat()),
                )

        week1_analytics = {
            "summary": {
                "total_prospects": 20,
                "total_pitches_sent": 20,
                "total_responses": len(RESPONSE_SCENARIOS),
                "overall_response_rate": 60.0,
                "total_bookings": 2,
                "interested_leads": 4,
                "avg_proposed_rate": 350,
                "follow_ups_sent": 16,
            },
            "venue_performance": {
                "Comedy Club": {"sent": 12, "responses": 8, "bookings": 2, "response_rate": 66.7, "booking_rate": 16.7},
                "Corporate Event": {"sent": 3, "responses": 1, "bookings": 1, "response_rate": 33.3, "booking_rate": 33.3},
                "College Venue": {"sent": 3, "responses": 2, "bookings": 0, "response_rate": 66.7, "booking_rate": 0},
                "Comedy Festival": {"sent": 2, "responses": 1, "bookings": 0, "response_rate": 50.0, "booking_rate": 0},
            },
        }
        week2_analytics = {
            "summary": {
                "total_prospects": 30,
                "total_pitches_sent": 30,
                "total_responses": len(RESPONSE_SCENARIOS) + 4,
                "overall_response_rate": 66.7,
                "total_bookings": 4,
                "interested_leads": 7,
                "avg_proposed_rate": 375,
                "follow_ups_sent": 22,
            },
            "venue_performance": {
                "Comedy Club": {"sent": 17, "responses": 12, "bookings": 3, "response_rate": 70.6, "booking_rate": 17.6},
                "Corporate Event": {"sent": 4, "responses": 2, "bookings": 1, "response_rate": 50.0, "booking_rate": 25.0},
                "College Venue": {"sent": 5, "responses": 3, "bookings": 0, "response_rate": 60.0, "booking_rate": 0},
                "Comedy Festival": {"sent": 4, "responses": 2, "bookings": 0, "response_rate": 50.0, "booking_rate": 0},
            },
            "ai_insights": {
                "top_insight": "Comedy clubs are converting at 70.6% — double down on this channel.",
                "effective_angles": [
                    "Mention recent performance video (YouTube reel)",
                    "Reference similar acts the venue has booked",
                    "Emphasize audience match for their crowd",
                ],
                "recommendations": [
                    {"action": "Raise rate to $400 for comedy clubs — accepted 75% of the time", "expected_impact": "+15% revenue per show", "priority": "high"},
                    {"action": "Create a corporate event package at $2000", "expected_impact": "3-5x revenue per booking", "priority": "high"},
                    {"action": "Apply to 5 more comedy festivals", "expected_impact": "Long-term brand building", "priority": "medium"},
                ],
                "rate_analysis": {
                    "current_rate_assessment": "slightly below market",
                    "suggested_adjustment": "Raise to $400 base, $450 for premium clubs",
                    "reasoning": "75% of venues accepted $350 without negotiation — you have room to increase.",
                },
                "focus_channels": ["Comedy Club", "College Venue"],
                "warning_flags": ["Corporate event outreach response rate is low — personalize more"],
            },
        }

        week1_date = (datetime.now() - timedelta(days=14)).isoformat()
        week2_date = (datetime.now() - timedelta(days=7)).isoformat()
        conn.execute("INSERT INTO analytics_snapshots (profile_id, snapshot_data, created_at) VALUES (?, ?, ?)",
                    (profile_id, json.dumps(week1_analytics), week1_date))
        conn.execute("INSERT INTO analytics_snapshots (profile_id, snapshot_data, created_at) VALUES (?, ?, ?)",
                    (profile_id, json.dumps(week2_analytics), week2_date))

        conn.commit()

    print(f"Seeded profile ID: {profile_id}")
    print(f"Created {len(PROSPECTS)} prospects, {len(pitch_ids)} week-1 pitches, {len(RESPONSE_SCENARIOS)} responses")
    print(f"Profile: Alex Rivera (comedian) — Los Angeles, CA")
    print(f"Use profile_id={profile_id} in the frontend")
    return profile_id


if __name__ == "__main__":
    seed()
