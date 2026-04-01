import pandas as pd

from app.strategy.base import Strategy, StrategyOutput


class DemoTrendStrategy(Strategy):
    def __init__(self, fast_window: int = 20, slow_window: int = 50, stop_loss_pct: float = 0.03) -> None:
        self.fast_window = fast_window
        self.slow_window = slow_window
        self.stop_loss_pct = stop_loss_pct

    def generate(self, frame: pd.DataFrame) -> StrategyOutput:
        close = frame["close"]
        fast_ma = close.rolling(self.fast_window).mean()
        slow_ma = close.rolling(self.slow_window).mean()

        long_condition = (fast_ma > slow_ma).astype(int)
        signals = long_condition.fillna(0)
        stop_prices = close * (1 - self.stop_loss_pct)

        return StrategyOutput(signals=signals, stop_prices=stop_prices)

