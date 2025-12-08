from datetime import datetime
from pydantic import BaseModel


class LogEntry(BaseModel):
    timestamp: datetime
    event_type: str
    user_email: str | None
    details: dict
    level: str
