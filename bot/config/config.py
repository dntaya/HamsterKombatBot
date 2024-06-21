from pydantic import field_validator, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict
from os import makedirs
from pathlib import Path
from bot.utils import logger

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)
    
    API_ID: int
    API_HASH: str

    ROOT_PATH: Path = Path(__file__).parents[2]
    PROFILE_DIR: Path = ROOT_PATH.joinpath('profiles')
    USE_PROXY_FROM_FILE: Path | None = None
    #USE_PROXY_FROM_FILE: Path = ROOT_PATH.joinpath('proxies.txt')

    WAIT_FOR_MOST_PROFIT_UPGRADES: bool = True

    AUTO_UPGRADE: bool = True

    AUTO_CLICKER: bool = True

    APPLY_DAILY_ENERGY: bool = True

    MIN_BALANCE: int = 1_000_000

    MIN_TAPS_FOR_CLICKER_IN_PERCENT: int = 80

    SLEEP_INTERVAL_BEFORE_UPGRADE: list[int] = [7, 30]

    BALANCE_STRATEGY: int = 10

    MAX_SLEEP_TIME: int = 10800

    DAILY_JSON_URL: str = "https://dntaya.github.io/HamsterKombatBot/daily_combo.json"
    
    @field_validator('PROFILE_DIR', mode='after')
    def profile_dir(field):
        # Make PROFILE_DIR if not exist
        try:
            makedirs(field, exist_ok=True)
        except Exception as error:
            logger.error('Unknown error while makedirs PROFILE_DIR')
            raise
        
        return field
    
    @field_validator('USE_PROXY_FROM_FILE', mode='before')
    def validate_path(path):
        
        if path:
            path = Path(path)
            if not path.exists():

                logger.error(f'Proxy file {path.resolve()} not found')
                raise FileNotFoundError
        
        return path

try:
    settings = Settings()
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))    
