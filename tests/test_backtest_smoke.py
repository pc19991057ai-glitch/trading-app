import pandas as pd

from app.backtest.engine import run_backtest
from app.strategy.demo_trend import DemoTrendStrategy


def test_backtest_smoke_returns_metrics() -> None:
    idx = pd.date_range("2024-01-01", periods=120, freq="D", tz="UTC")
    close = pd.Series(range(100, 220), index=idx, dtype="float64")
    frame = pd.DataFrame(
        {
            "open": close,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": 1000.0,
        },
        index=idx,
    )

    result = run_backtest(
        symbol="TEST",
        frame=frame,
        strategy=DemoTrendStrategy(fast_window=5, slow_window=10, stop_loss_pct=0.02),
        initial_capital=100000,
        risk_per_trade=0.01,
        max_drawdown_limit=0.15,
        commission_bps=0,
        slippage_bps=0,
    )

    assert result.symbol == "TEST"
    assert result.ending_equity > 0
    assert result.max_drawdown <= 0

