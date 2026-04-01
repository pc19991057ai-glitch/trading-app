import numpy as np
import pandas as pd


def max_drawdown(equity_curve: pd.Series) -> float:
    rolling_peak = equity_curve.cummax()
    drawdown = (equity_curve - rolling_peak) / rolling_peak
    return float(drawdown.min())


def average_monthly_return(equity_curve: pd.Series) -> float:
    monthly = equity_curve.resample("ME").last().pct_change().dropna()
    if monthly.empty:
        return 0.0
    return float(monthly.mean())


def sharpe_ratio(equity_curve: pd.Series) -> float:
    returns = equity_curve.pct_change().dropna()
    if returns.empty or np.isclose(returns.std(), 0.0):
        return 0.0
    return float((returns.mean() / returns.std()) * np.sqrt(252))

