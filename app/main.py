from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.backtest.engine import run_backtest
from app.config import settings
from app.data.registry import DataRegistry
from app.strategy.demo_trend import DemoTrendStrategy

app = FastAPI(title="trading-app", version="0.1.0")
registry = DataRegistry()


class BacktestRequest(BaseModel):
    symbols: list[str] = Field(default_factory=list)
    interval: str | None = None
    start: datetime | None = None
    end: datetime | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/symbols")
def symbols() -> dict[str, list[str]]:
    return {"symbols": settings.symbols}


@app.post("/backtest")
def backtest(payload: BacktestRequest) -> dict:
    symbols = payload.symbols or settings.symbols
    interval = payload.interval or settings.default_interval

    start = payload.start or datetime.fromisoformat(settings.default_start)
    end = payload.end or datetime.fromisoformat(settings.default_end)

    strategy = DemoTrendStrategy()
    results = []

    for symbol in symbols:
        try:
            market_data = registry.fetch(symbol=symbol, interval=interval, start=start, end=end)
            result = run_backtest(
                symbol=market_data.symbol,
                frame=market_data.frame,
                strategy=strategy,
                initial_capital=settings.initial_capital,
                risk_per_trade=settings.risk_per_trade,
                max_drawdown_limit=settings.max_drawdown,
                commission_bps=settings.commission_bps,
                slippage_bps=settings.slippage_bps,
            )
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"{symbol}: {exc}") from exc

        results.append(
            {
                "symbol": result.symbol,
                "trades": result.trades,
                "ending_equity": result.ending_equity,
                "max_drawdown": result.max_drawdown,
                "average_monthly_return": result.average_monthly_return,
                "sharpe_ratio": result.sharpe_ratio,
                "halted_by_drawdown": result.halted_by_drawdown,
            }
        )

    return {
        "target_monthly_return": 0.02,
        "risk_per_trade": settings.risk_per_trade,
        "max_drawdown_limit": settings.max_drawdown,
        "results": results,
    }

