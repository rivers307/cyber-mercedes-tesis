from datetime import datetime

from pydantic import BaseModel


class Status(BaseModel):
    status: str
    last_updated: datetime
    confidence: float
    verified: bool
    sources: list[str]
    is_preliminary: bool
    stale: bool
