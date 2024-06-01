from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

    API_ID: int
    API_HASH: str

    MIN_AVAILABLE_TAPS: int = 15
    WAIT_FOR_MOST_PROFIT_UPGRADES: bool = True

    AUTO_UPGRADE: bool = True

    AUTO_CLICKER: bool = True

    APPLY_DAILY_ENERGY: bool = True

    SLEEP_BETWEEN_TAP: list[int] = [10, 25]

    USE_PROXY_FROM_FILE: bool = False


settings = Settings()
