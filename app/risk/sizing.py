def position_size_from_stop(
    equity: float,
    entry_price: float,
    stop_price: float,
    risk_per_trade: float = 0.01,
) -> float:
    if equity <= 0:
        raise ValueError("equity must be > 0")
    if not (0 < risk_per_trade < 1):
        raise ValueError("risk_per_trade must be between 0 and 1")

    per_unit_risk = abs(entry_price - stop_price)
    if per_unit_risk <= 0:
        return 0.0

    risk_cash = equity * risk_per_trade
    size = risk_cash / per_unit_risk
    return max(size, 0.0)

