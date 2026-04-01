from datetime import datetime
from typing import Protocol

from app.data.types import MarketData


class DataSource(Protocol):
    def fetch_ohlcv(
        self,
        symbol: str,
        interval: str,
        start: datetime,
        end: datetime,
    ) -> MarketData:
        ...

