import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "booking.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    entertainer_type TEXT NOT NULL,
    genre_style TEXT,
    experience_years INTEGER DEFAULT 0,
    shows_count INTEGER DEFAULT 0,
    location TEXT,
    touring_region TEXT,
    rate_min REAL DEFAULT 0,
    rate_max REAL DEFAULT 0,
    youtube_url TEXT,
    instagram_url TEXT,
    instagram_followers INTEGER DEFAULT 0,
    bio TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS market_research (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL,
    research_data TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (profile_id) REFERENCES profiles(id)
);

CREATE TABLE IF NOT EXISTS prospects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    location TEXT,
    contact_email TEXT,
    contact_name TEXT,
    typical_pay_min REAL DEFAULT 0,
    typical_pay_max REAL DEFAULT 0,
    notes TEXT,
    status TEXT DEFAULT 'new',
    source TEXT DEFAULT 'manual',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (profile_id) REFERENCES profiles(id)
);

CREATE TABLE IF NOT EXISTS pitches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prospect_id INTEGER NOT NULL,
    profile_id INTEGER NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    proposed_rate REAL DEFAULT 0,
    status TEXT DEFAULT 'draft',
    sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (prospect_id) REFERENCES prospects(id),
    FOREIGN KEY (profile_id) REFERENCES profiles(id)
);

CREATE TABLE IF NOT EXISTS pitch_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pitch_id INTEGER NOT NULL,
    prospect_id INTEGER NOT NULL,
    response_type TEXT NOT NULL,
    response_text TEXT,
    responded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pitch_id) REFERENCES pitches(id),
    FOREIGN KEY (prospect_id) REFERENCES prospects(id)
);

CREATE TABLE IF NOT EXISTS follow_ups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pitch_id INTEGER NOT NULL,
    prospect_id INTEGER NOT NULL,
    profile_id INTEGER NOT NULL,
    sequence_number INTEGER NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    scheduled_for TIMESTAMP,
    sent_at TIMESTAMP,
    status TEXT DEFAULT 'scheduled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pitch_id) REFERENCES pitches(id),
    FOREIGN KEY (prospect_id) REFERENCES prospects(id),
    FOREIGN KEY (profile_id) REFERENCES profiles(id)
);

CREATE TABLE IF NOT EXISTS analytics_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL,
    snapshot_data TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (profile_id) REFERENCES profiles(id)
);
"""


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(SCHEMA)
        conn.commit()


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def row_to_dict(row):
    if row is None:
        return None
    return dict(row)


def rows_to_list(rows):
    return [dict(r) for r in rows]
