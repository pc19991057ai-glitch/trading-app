from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
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


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>trading-app backtest UI</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
  </head>
  <body class="bg-slate-950 text-slate-100 min-h-screen">
    <div class="max-w-6xl mx-auto py-8 px-4">
      <h1 class="text-3xl font-semibold mb-6">Trading Backtest Console</h1>
      <div class="grid md:grid-cols-3 gap-6 mb-8">
        <div class="md:col-span-2 space-y-4">
          <div>
            <label class="block text-sm mb-1">Symbols (comma separated)</label>
            <input id="symbols-input" class="w-full rounded border border-slate-700 bg-slate-900 px-3 py-2 text-sm" placeholder="BTCUSDT,AAPL,QQQ" />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm mb-1">Start</label>
              <input id="start-input" type="date" class="w-full rounded border border-slate-700 bg-slate-900 px-3 py-2 text-sm" />
            </div>
            <div>
              <label class="block text-sm mb-1">End</label>
              <input id="end-input" type="date" class="w-full rounded border border-slate-700 bg-slate-900 px-3 py-2 text-sm" />
            </div>
          </div>
          <div class="grid grid-cols-3 gap-4">
            <div>
              <label class="block text-sm mb-1">Interval</label>
              <select id="interval-input" class="w-full rounded border border-slate-700 bg-slate-900 px-3 py-2 text-sm">
                <option value="1d">1d</option>
                <option value="4h">4h</option>
                <option value="1h">1h</option>
              </select>
            </div>
            <div>
              <label class="block text-sm mb-1">Risk / trade</label>
              <input id="risk-input" type="number" step="0.001" min="0.001" max="0.05" class="w-full rounded border border-slate-700 bg-slate-900 px-3 py-2 text-sm" />
            </div>
            <div>
              <label class="block text-sm mb-1">Max DD</label>
              <input id="dd-input" type="number" step="0.01" min="0.05" max="0.5" class="w-full rounded border border-slate-700 bg-slate-900 px-3 py-2 text-sm" />
            </div>
          </div>
          <button id="run-btn" class="inline-flex items-center gap-2 rounded bg-emerald-500 px-4 py-2 text-sm font-medium text-slate-900 hover:bg-emerald-400">
            Run backtest
          </button>
          <p id="status" class="text-xs text-slate-400 mt-1"></p>
        </div>
        <div class="space-y-2 text-xs bg-slate-900 border border-slate-800 rounded p-3">
          <p class="font-semibold mb-1">Notes</p>
          <ul class="list-disc pl-4 space-y-1">
            <li>Historical backtest only, no live trading.</li>
            <li>Risk per trade ≤ 1% of equity.</li>
            <li>Max portfolio drawdown 15% halts new trades.</li>
          </ul>
        </div>
      </div>
      <div class="bg-slate-900 border border-slate-800 rounded p-4 mb-6 overflow-x-auto">
        <table class="min-w-full text-xs" id="results-table">
          <thead class="text-slate-300 border-b border-slate-800">
            <tr>
              <th class="text-left py-2 pr-4">Symbol</th>
              <th class="text-right py-2 pr-4">Trades</th>
              <th class="text-right py-2 pr-4">End Equity</th>
              <th class="text-right py-2 pr-4">Avg Monthly %</th>
              <th class="text-right py-2 pr-4">Max DD %</th>
              <th class="text-right py-2 pr-4">Sharpe</th>
              <th class="text-right py-2 pr-4">Halted</th>
            </tr>
          </thead>
          <tbody id="results-body" class="divide-y divide-slate-800"></tbody>
        </table>
      </div>
      <div class="bg-slate-900 border border-slate-800 rounded p-4">
        <h2 class="text-sm font-medium mb-3">Equity curve (first symbol)</h2>
        <canvas id="equity-chart" height="120"></canvas>
      </div>
    </div>
    <script>
      const symbolsInput = document.getElementById("symbols-input");
      const startInput = document.getElementById("start-input");
      const endInput = document.getElementById("end-input");
      const intervalInput = document.getElementById("interval-input");
      const riskInput = document.getElementById("risk-input");
      const ddInput = document.getElementById("dd-input");
      const statusEl = document.getElementById("status");
      const tbody = document.getElementById("results-body");
      let chart;

      async function loadDefaults() {
        try {
          const res = await fetch("/symbols");
          const data = await res.json();
          symbolsInput.value = data.symbols.join(",");
        } catch (e) {
          console.error(e);
        }
      }

      function renderTable(results) {
        tbody.innerHTML = "";
        for (const row of results) {
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td class="py-2 pr-4">${row.symbol}</td>
            <td class="py-2 pr-4 text-right">${row.trades}</td>
            <td class="py-2 pr-4 text-right">${row.ending_equity.toFixed(2)}</td>
            <td class="py-2 pr-4 text-right">${(row.average_monthly_return * 100).toFixed(2)}</td>
            <td class="py-2 pr-4 text-right">${(row.max_drawdown * 100).toFixed(2)}</td>
            <td class="py-2 pr-4 text-right">${row.sharpe_ratio.toFixed(2)}</td>
            <td class="py-2 pr-4 text-right">${row.halted_by_drawdown ? "Yes" : "No"}</td>
          `;
          tbody.appendChild(tr);
        }
      }

      function renderChart(results) {
        const first = results[0];
        if (!first || !first.equity_curve) {
          return;
        }
        const labels = first.equity_curve.map((p) => p[0]);
        const values = first.equity_curve.map((p) => p[1]);
        const ctx = document.getElementById("equity-chart").getContext("2d");
        if (chart) {
          chart.destroy();
        }
        chart = new Chart(ctx, {
          type: "line",
          data: {
            labels,
            datasets: [
              {
                label: first.symbol,
                data: values,
                borderColor: "rgb(16, 185, 129)",
                borderWidth: 2,
                pointRadius: 0,
              },
            ],
          },
          options: {
            responsive: true,
            scales: {
              x: {
                ticks: { display: false },
              },
              y: {
                ticks: { color: "#cbd5f5" },
              },
            },
          },
        });
      }

      document.getElementById("run-btn").addEventListener("click", async () => {
        statusEl.textContent = "Running backtest...";
        try {
          const symbolsRaw = symbolsInput.value.trim();
          const symbols =
            symbolsRaw.length > 0
              ? symbolsRaw.split(",").map((s) => s.trim()).filter(Boolean)
              : [];
          const payload = {
            symbols,
            interval: intervalInput.value || null,
            start: startInput.value ? startInput.value + "T00:00:00" : null,
            end: endInput.value ? endInput.value + "T00:00:00" : null,
          };
          const params = new URLSearchParams();
          params.set("include_equity", "true");
          if (riskInput.value) {
            params.set("risk_per_trade", riskInput.value);
          }
          if (ddInput.value) {
            params.set("max_drawdown", ddInput.value);
          }

          const res = await fetch("/backtest?" + params.toString(), {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          });
          if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || "Request failed");
          }
          const data = await res.json();
          renderTable(data.results);
          renderChart(data.results);
          statusEl.textContent = "Done.";
        } catch (e) {
          console.error(e);
          statusEl.textContent = "Error: " + e.message;
        }
      });

      loadDefaults();
    </script>
  </body>
</html>
    """


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/symbols")
def symbols() -> dict[str, list[str]]:
    return {"symbols": settings.symbols}


@app.post("/backtest")
def backtest(
    payload: BacktestRequest,
    include_equity: bool = False,
    risk_per_trade: float | None = None,
    max_drawdown: float | None = None,
) -> dict:
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
                risk_per_trade=risk_per_trade or settings.risk_per_trade,
                max_drawdown_limit=max_drawdown or settings.max_drawdown,
                commission_bps=settings.commission_bps,
                slippage_bps=settings.slippage_bps,
            )
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"{symbol}: {exc}") from exc

        payload_dict: dict = {
            "symbol": result.symbol,
            "trades": result.trades,
            "ending_equity": result.ending_equity,
            "max_drawdown": result.max_drawdown,
            "average_monthly_return": result.average_monthly_return,
            "sharpe_ratio": result.sharpe_ratio,
            "halted_by_drawdown": result.halted_by_drawdown,
        }
        if include_equity:
            payload_dict["equity_curve"] = [
                (ts.isoformat(), float(v)) for ts, v in result.equity_curve.items()
            ]
        results.append(payload_dict)

    return {
        "target_monthly_return": 0.02,
        "risk_per_trade": settings.risk_per_trade,
        "max_drawdown_limit": settings.max_drawdown,
        "results": results,
    }

