from datetime import date

import httpx

from .exceptions import TasaVEError
from .models import BcvRate, ConvertResult, HistoryEntry, ParallelRate, Rate, Status

_BASE_URL = "https://tasave.sudelca.com"


class AsyncRatesResource:
    def __init__(self, http: httpx.AsyncClient):
        self._http = http

    async def current(self) -> Rate:
        return Rate.model_validate(await _get(self._http, "/v1/rates"))

    async def bcv(self) -> BcvRate:
        return BcvRate.model_validate(await _get(self._http, "/v1/rates/bcv"))

    async def parallel(self) -> ParallelRate:
        return ParallelRate.model_validate(await _get(self._http, "/v1/rates/parallel"))


class AsyncHistoryResource:
    def __init__(self, http: httpx.AsyncClient):
        self._http = http

    async def range(self, from_date: date | str, to_date: date | str) -> list[HistoryEntry]:
        rows = await _get(self._http, "/v1/history", params={"from": str(from_date), "to": str(to_date)})
        return [HistoryEntry.model_validate(r) for r in rows]

    async def date(self, d: date | str) -> HistoryEntry:
        return HistoryEntry.model_validate(await _get(self._http, f"/v1/history/{d}"))


class AsyncTasaVE:
    """Asynchronous TasaVE client.

    Usage::

        async with AsyncTasaVE() as client:
            rate = await client.rates.current()
            print(rate.bcv_usd)
    """

    def __init__(self, api_key: str | None = None, base_url: str = _BASE_URL):
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self._http = httpx.AsyncClient(base_url=base_url, headers=headers, timeout=10)
        self.rates = AsyncRatesResource(self._http)
        self.history = AsyncHistoryResource(self._http)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        await self._http.aclose()

    async def aclose(self):
        await self._http.aclose()

    async def convert(
        self,
        amount: float,
        from_currency: str,
        to: str,
        source: str = "bcv",
    ) -> ConvertResult:
        return ConvertResult.model_validate(
            await _get(self._http, "/v1/convert", params={
                "amount": amount, "from": from_currency, "to": to, "source": source,
            })
        )

    async def status(self) -> Status:
        return Status.model_validate(await _get(self._http, "/v1/status"))


async def _get(http: httpx.AsyncClient, path: str, params: dict | None = None):
    resp = await http.get(path, params=params)
    if not resp.is_success:
        raise TasaVEError(resp.status_code, resp.text)
    return resp.json()
