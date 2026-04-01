from dataclasses import dataclass

import pandas as pd

from app.backtest.metrics import average_monthly_return, max_drawdown, sharpe_ratio
from app.risk.drawdown import breached_max_drawdown
from app.risk.sizing import position_size_from_stop
from app.strategy.base import Strategy


@dataclass(slots=True)
class BacktestResult:
    symbol: str
    trades: int
    ending_equity: float
    max_drawdown: float
    average_monthly_return: float
    sharpe_ratio: float
    halted_by_drawdown: bool
    equity_curve: pd.Series


def _apply_cost(price: float, bps: float, is_buy: bool) -> float:
    sign = 1 if is_buy else -1
    return price * (1 + sign * (bps / 10000.0))


def run_backtest(
    symbol: str,
    frame: pd.DataFrame,
    strategy: Strategy,
    initial_capital: float,
    risk_per_trade: float,
    max_drawdown_limit: float,
    commission_bps: float,
    slippage_bps: float,
) -> BacktestResult:
    frame = frame.copy().dropna()
    output = strategy.generate(frame)

    equity = initial_capital
    peak_equity = equity
    halted = False

    position_size = 0.0
    entry_price = 0.0
    trades = 0

    equity_curve: list[float] = []
    equity_index: list[pd.Timestamp] = []

    for idx in frame.index:
        close = float(frame.at[idx, "close"])
        signal = int(output.signals.loc[idx])
        stop_price = float(output.stop_prices.loc[idx])

        if position_size > 0:
            mark_to_market = equity - (position_size * entry_price) + (position_size * close)
        else:
            mark_to_market = equity

        peak_equity = max(peak_equity, mark_to_market)
        if breached_max_drawdown(mark_to_market, peak_equity, max_drawdown_limit):
            halted = True
            if position_size > 0:
                exit_price = _apply_cost(close, commission_bps + slippage_bps, is_buy=False)
                equity = equity - (position_size * entry_price) + (position_size * exit_price)
                position_size = 0.0
                entry_price = 0.0
            equity_curve.append(equity)
            equity_index.append(idx)
            break

        if halted:
            equity_curve.append(mark_to_market)
            equity_index.append(idx)
            continue

        if position_size > 0 and close <= stop_price:
            exit_price = _apply_cost(close, commission_bps + slippage_bps, is_buy=False)
            equity = equity - (position_size * entry_price) + (position_size * exit_price)
            position_size = 0.0
            entry_price = 0.0
            trades += 1

        if signal == 1 and position_size == 0:
            size = position_size_from_stop(
                equity=equity,
                entry_price=close,
                stop_price=stop_price,
                risk_per_trade=risk_per_trade,
            )
            if size > 0:
                fill_price = _apply_cost(close, commission_bps + slippage_bps, is_buy=True)
                cash_needed = size * fill_price
                if cash_needed <= equity:
                    position_size = size
                    entry_price = fill_price

        if signal == 0 and position_size > 0:
            exit_price = _apply_cost(close, commission_bps + slippage_bps, is_buy=False)
            equity = equity - (position_size * entry_price) + (position_size * exit_price)
            position_size = 0.0
            entry_price = 0.0
            trades += 1

        if position_size > 0:
            mark_to_market = equity - (position_size * entry_price) + (position_size * close)
        else:
            mark_to_market = equity

        equity_curve.append(mark_to_market)
        equity_index.append(idx)

    if position_size > 0:
        final_close = float(frame.iloc[-1]["close"])
        exit_price = _apply_cost(final_close, commission_bps + slippage_bps, is_buy=False)
        equity = equity - (position_size * entry_price) + (position_size * exit_price)
        trades += 1
    else:
        equity = equity_curve[-1] if equity_curve else equity

    equity_series = pd.Series(equity_curve, index=pd.DatetimeIndex(equity_index), dtype="float64")
    if equity_series.empty:
        equity_series = pd.Series([initial_capital], index=[frame.index[0]], dtype="float64")

    result = BacktestResult(
        symbol=symbol,
        trades=trades,
        ending_equity=float(equity),
        max_drawdown=max_drawdown(equity_series),
        average_monthly_return=average_monthly_return(equity_series),
        sharpe_ratio=sharpe_ratio(equity_series),
        halted_by_drawdown=halted,
        equity_curve=equity_series,
    )

    return result

