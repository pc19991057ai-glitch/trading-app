from datetime import datetime

import httpx
import pandas as pd

from app.data.sources.base import DataSource
from app.data.types import MarketData, normalize_ohlcv


class BinancePublicSource(DataSource):
    base_url = "https://api.binance.com/api/v3/klines"

    def fetch_ohlcv(
        self,
        symbol: str,
        interval: str,
        start: datetime,
        end: datetime,
    ) -> MarketData:
        params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "startTime": int(start.timestamp() * 1000),
            "endTime": int(end.timestamp() * 1000),
            "limit": 1000,
        }
        with httpx.Client(timeout=20.0) as client:
            resp = client.get(self.base_url, params=params)
            resp.raise_for_status()
            raw = resp.json()

        if not raw:
            raise ValueError(f"No data from Binance for symbol={symbol}")

        frame = pd.DataFrame(
            raw,
            columns=[
                "open_time",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "close_time",
                "quote_asset_volume",
                "number_of_trades",
                "taker_buy_base_asset_volume",
                "taker_buy_quote_asset_volume",
                "ignore",
            ],
        )
        frame["open_time"] = pd.to_datetime(frame["open_time"], unit="ms", utc=True)
        frame = frame.set_index("open_time")
        for col in ["open", "high", "low", "close", "volume"]:
            frame[col] = frame[col].astype(float)

        return normalize_ohlcv(frame, symbol, interval)

