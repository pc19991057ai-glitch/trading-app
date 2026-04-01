from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    default_symbols: str = "BTCUSDT,AAPL,QQQ"
    default_interval: str = "1d"
    default_start: str = "2023-01-01"
    default_end: str = "2024-12-31"
    initial_capital: float = 100000.0
    risk_per_trade: float = 0.01
    max_drawdown: float = 0.15
    commission_bps: float = 5.0
    slippage_bps: float = 2.0

    @property
    def symbols(self) -> list[str]:
        return [s.strip().upper() for s in self.default_symbols.split(",") if s.strip()]


settings = Settings()

