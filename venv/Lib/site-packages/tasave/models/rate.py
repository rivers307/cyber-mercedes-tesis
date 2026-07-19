from datetime import date, datetime

from pydantic import BaseModel


class Rate(BaseModel):
    bcv_usd: float
    bcv_eur: float | None = None
    parallel_usdt: float | None = None
    parallel_buy: float | None = None
    parallel_sell: float | None = None
    confidence: float
    verified: bool
    checked_against: list[str]
    valid_from: datetime
    valid_until: datetime
    next_expected_update: datetime
    next_business_day: date
    is_preliminary: bool
    official_since: datetime | None = None
    published_at: datetime | None = None
    sources: list[str]
    consensus: bool
    updated_at: datetime
    stale: bool | None = None
    stale_since: datetime | None = None


class BcvRate(BaseModel):
    bcv_usd: float
    bcv_eur: float | None = None
    confidence: float
    verified: bool
    valid_from: datetime
    valid_until: datetime
    next_expected_update: datetime
    next_business_day: date
    is_preliminary: bool
    official_since: datetime | None = None
    published_at: datetime | None = None
    sources: list[str]
    updated_at: datetime
    stale: bool | None = None


class ParallelRate(BaseModel):
    parallel_usdt: float | None = None
    parallel_buy: float | None = None
    parallel_sell: float | None = None
    sources: list[str]
    updated_at: datetime


class HistoryEntry(BaseModel):
    date: date
    bcv_usd: float
    bcv_eur: float | None = None
    parallel_usdt: float | None = None
    confidence: float
    sources: list[str]
