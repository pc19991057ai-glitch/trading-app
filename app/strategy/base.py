from dataclasses import dataclass

import pandas as pd


@dataclass(slots=True)
class StrategyOutput:
    signals: pd.Series
    stop_prices: pd.Series


class Strategy:
    def generate(self, frame: pd.DataFrame) -> StrategyOutput:
        raise NotImplementedError

