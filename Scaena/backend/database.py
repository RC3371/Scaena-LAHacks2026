from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./scaena.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from backend.models import Base as ModelsBase
    ModelsBase.metadata.create_all(bind=engine)
    _ensure_sqlite_columns()


def _ensure_sqlite_columns():
    """Tiny dev migration helper for the hackathon SQLite database."""
    if not DATABASE_URL.startswith("sqlite"):
        return

    columns = {
        "venues": {
            "contact_name": "contact_name VARCHAR",
            "contact_email": "contact_email VARCHAR",
            "source_url": "source_url VARCHAR",
        },
        "pitches": {
            "recipient_email": "recipient_email VARCHAR",
            "gmail_message_id": "gmail_message_id VARCHAR",
            "gmail_thread_id": "gmail_thread_id VARCHAR",
        },
        "gmail_accounts": {
            "last_sync_at": "last_sync_at DATETIME",
        },
        "conversation_messages": {
            "gmail_message_id": "gmail_message_id VARCHAR",
            "gmail_thread_id": "gmail_thread_id VARCHAR",
            "from_email": "from_email VARCHAR",
        },
        "bookings": {
            "logistics_checklist": "logistics_checklist TEXT",
            "post_show_notes": "post_show_notes TEXT",
            "crowd_size": "crowd_size INTEGER",
            "audience_reaction": "audience_reaction VARCHAR",
            "payout_received": "payout_received BOOLEAN DEFAULT 0",
            "venue_satisfaction": "venue_satisfaction VARCHAR",
            "rebook_recommended": "rebook_recommended BOOLEAN",
            "next_reminder_at": "next_reminder_at DATETIME",
            "performance_completed_at": "performance_completed_at DATETIME",
            "updated_at": "updated_at DATETIME",
        },
    }

    with engine.begin() as conn:
        for table_name, wanted in columns.items():
            existing = {
                row[1]
                for row in conn.exec_driver_sql(f"PRAGMA table_info({table_name})").fetchall()
            }
            for column_name, definition in wanted.items():
                if column_name not in existing:
                    conn.exec_driver_sql(f"ALTER TABLE {table_name} ADD COLUMN {definition}")
