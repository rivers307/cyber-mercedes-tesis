from datetime import date

import httpx

from .exceptions import TasaVEError
from .models import BcvRate, ConvertResult, HistoryEntry, ParallelRate, Rate, Status

_BASE_URL = "https://tasave.sudelca.com"


class RatesResource:
    def __init__(self, http: httpx.Client):
        self._http = http

    def current(self) -> Rate:
        return Rate.model_validate(_get(self._http, "/v1/rates"))

    def bcv(self) -> BcvRate:
        return BcvRate.model_validate(_get(self._http, "/v1/rates/bcv"))

    def parallel(self) -> ParallelRate:
        return ParallelRate.model_validate(_get(self._http, "/v1/rates/parallel"))


class HistoryResource:
    def __init__(self, http: httpx.Client):
        self._http = http

    def range(self, from_date: date | str, to_date: date | str) -> list[HistoryEntry]:
        rows = _get(self._http, "/v1/history", params={"from": str(from_date), "to": str(to_date)})
        return [HistoryEntry.model_validate(r) for r in rows]

    def date(self, d: date | str) -> HistoryEntry:
        return HistoryEntry.model_validate(_get(self._http, f"/v1/history/{d}"))


class TasaVE:
    """Synchronous TasaVE client.

    Usage::

        client = TasaVE()
        rate = client.rates.current()
        print(rate.bcv_usd)

        client = TasaVE(api_key="...")
        history = client.history.range("2026-01-01", "2026-06-20")
    """

    def __init__(self, api_key: str | None = None, base_url: str = _BASE_URL):
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self._http = httpx.Client(base_url=base_url, headers=headers, timeout=10)
        self.rates = RatesResource(self._http)
        self.history = HistoryResource(self._http)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self._http.close()

    def close(self):
        self._http.close()

    def convert(
        self,
        amount: float,
        from_currency: str,
        to: str,
        source: str = "bcv",
    ) -> ConvertResult:
        return ConvertResult.model_validate(
            _get(self._http, "/v1/convert", params={
                "amount": amount, "from": from_currency, "to": to, "source": source,
            })
        )

    def status(self) -> Status:
        return Status.model_validate(_get(self._http, "/v1/status"))


def _get(http: httpx.Client, path: str, params: dict | None = None):
    resp = http.get(path, params=params)
    if not resp.is_success:
        raise TasaVEError(resp.status_code, resp.text)
    return resp.json()
