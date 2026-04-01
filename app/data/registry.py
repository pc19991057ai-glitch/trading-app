from datetime import datetime

from app.data.sources.base import DataSource
from app.data.sources.binance_public import BinancePublicSource
from app.data.sources.yfinance_source import YFinanceSource
from app.data.types import MarketData


class DataRegistry:
    def __init__(self) -> None:
        self.binance = BinancePublicSource()
        self.yfinance = YFinanceSource()

    @staticmethod
    def _is_binance_symbol(symbol: str) -> bool:
        upper = symbol.upper()
        suffixes = ("USDT", "BUSD", "BTC", "ETH")
        return upper.endswith(suffixes) and "/" not in upper

    def resolve_source(self, symbol: str) -> DataSource:
        if self._is_binance_symbol(symbol):
            return self.binance
        return self.yfinance

    def fetch(
        self,
        symbol: str,
        interval: str,
        start: datetime,
        end: datetime,
    ) -> MarketData:
        source = self.resolve_source(symbol)
        return source.fetch_ohlcv(symbol=symbol, interval=interval, start=start, end=end)

