# trading-app

可放上 GitHub、可部署到 Zeabur 的多資產回測 API 專案。  
第一版只做歷史回測，不含真實下單。

## 功能

- 多資料源抽象（目前支援 `yfinance` 與 Binance 公開 K 線）
- 回測風控：
  - 每筆交易最大風險 `1%`（依 entry-stop 距離算倉位）
  - 組合最大回撤 `15%` 觸發停機
- 回測報表：`average_monthly_return`、`max_drawdown`、`sharpe_ratio`

## 本機執行

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -e .[dev]
uvicorn app.main:app --reload
```

啟動後可測試：

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/symbols
curl -X POST http://127.0.0.1:8000/backtest -H "Content-Type: application/json" -d "{}"
```

## Docker

```bash
docker build -t trading-app .
docker run -p 8000:8000 --env-file .env.example trading-app
```

## Zeabur 部署

1. 把專案 push 到 GitHub。
2. 在 Zeabur 新增 Service，選取這個 repo。
3. 使用 `Dockerfile` 部署。
4. 設定環境變數（可先用 `.env.example` 內容）。
5. Zeabur 會注入 `PORT`，服務以 `uvicorn app.main:app` 啟動。

## API

- `GET /health`
- `GET /symbols`
- `POST /backtest`

`POST /backtest` body 範例：

```json
{
  "symbols": ["BTCUSDT", "AAPL"],
  "interval": "1d",
  "start": "2023-01-01T00:00:00",
  "end": "2024-12-31T00:00:00"
}
```

## 重要說明

- `2%/mon` 為歷史回測目標參考，不是未來保證。
- yfinance 與 Binance 公開 API 皆可能有 rate limit。
- 未完整納入實盤摩擦（交易稅、借券、深度衝擊）時，績效可能偏樂觀。

