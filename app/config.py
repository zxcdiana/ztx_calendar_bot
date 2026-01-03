from pathlib import Path
from pydantic import Field, Secret
from pydantic_settings import BaseSettings, SettingsConfigDict


import platformdirs


APP_DIR = Path(__file__).parent.parent
CONFIG_DIR = platformdirs.user_config_path("ztx_calendar_bot", ensure_exists=True)
DATABASE_PATH = CONFIG_DIR / "database.sqlite3"
LOCALES_DIR = APP_DIR / "locales/"


class AppConfig(BaseSettings):
    owners: list[int]
    bot_token: Secret[str]
    database_uri: Secret[str] = Field(
        default=Secret[str](f"sqlite+aiosqlite:///{DATABASE_PATH}")
    )
    locale: str = "ru"

    model_config = SettingsConfigDict(env_file=".env")


app_cfg = AppConfig.model_validate({})
