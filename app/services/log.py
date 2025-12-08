from datetime import datetime, timezone

from app.database import get_database
from app.models.log import LogEntry


def log_event(
    event_type: str,
    level: str = "info",
    user_email: str | None = None,
    details: dict | None = None
) -> None:
    log_entry = LogEntry(
        timestamp=datetime.now(timezone.utc),
        event_type=event_type,
        user_email=user_email,
        details=details or {},
        level=level
    )
    db = get_database()
    db.logs.insert_one(log_entry.model_dump())
