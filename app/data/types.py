from dataclasses import dataclass

import pandas as pd


@dataclass(slots=True)
class MarketData:
    symbol: str
    timeframe: str
    frame: pd.DataFrame


def normalize_ohlcv(df: pd.DataFrame, symbol: str, timeframe: str) -> MarketData:
    required_cols = ["open", "high", "low", "close", "volume"]
    source = df.copy()
    source.columns = [str(c).lower() for c in source.columns]

    missing = [col for col in required_cols if col not in source.columns]
    if missing:
        raise ValueError(f"Missing OHLCV columns: {missing}")

    result = source[required_cols].dropna().sort_index()
    if not isinstance(result.index, pd.DatetimeIndex):
        result.index = pd.to_datetime(result.index, utc=True)
    elif result.index.tz is None:
        result.index = result.index.tz_localize("UTC")
    else:
        result.index = result.index.tz_convert("UTC")

    return MarketData(symbol=symbol.upper(), timeframe=timeframe, frame=result)

