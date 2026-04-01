def drawdown_ratio(current_equity: float, peak_equity: float) -> float:
    if peak_equity <= 0:
        raise ValueError("peak_equity must be > 0")
    return (current_equity - peak_equity) / peak_equity


def breached_max_drawdown(current_equity: float, peak_equity: float, max_drawdown: float) -> bool:
    if not (0 < max_drawdown < 1):
        raise ValueError("max_drawdown must be between 0 and 1")
    return drawdown_ratio(current_equity, peak_equity) <= -max_drawdown

