from datetime import datetime

from pydantic import BaseModel


class ConvertResult(BaseModel):
    amount: float
    from_currency: str
    to_currency: str
    result: float
    rate: float
    source: str
    rate_updated_at: datetime
