from datetime import datetime

import yfinance as yf

from app.data.sources.base import DataSource
from app.data.types import MarketData, normalize_ohlcv


class YFinanceSource(DataSource):
    def fetch_ohlcv(
        self,
        symbol: str,
        interval: str,
        start: datetime,
        end: datetime,
    ) -> MarketData:
        ticker = yf.Ticker(symbol)
        frame = ticker.history(interval=interval, start=start, end=end, auto_adjust=False)
        if frame.empty:
            raise ValueError(f"No data from yfinance for symbol={symbol}")
        return normalize_ohlcv(frame, symbol, interval)

