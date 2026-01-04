from __future__ import annotations

from typing import Literal
from pathlib import Path
import platformdirs
import logging

from pydantic import Secret, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from aiogram import Bot, Dispatcher, Router
from aiogram.fsm.storage.memory import SimpleEventIsolation

from app.i18n import FluentRuntimeCore, I18nMiddleware, I18nMiddlewareManager


APP_DIR = Path(__file__).parent.parent
CONFIG_DIR = platformdirs.user_config_path("ztx_calendar_bot", ensure_exists=True)
DATABASE_PATH = CONFIG_DIR / "database.sqlite3"
_LOCAL_DATABASE_URI = f"sqlite+aiosqlite:///{DATABASE_PATH}"
LOCALES_DIR = APP_DIR / "locales/"


dp = Dispatcher(events_isolation=SimpleEventIsolation())
main_router = dp.include_router(Router())
commands_router = main_router.include_router(Router())
mood_router = commands_router.include_router(Router())
admin_router = commands_router.include_router(Router())


class AppConfig(BaseSettings):
    owners: set[int]
    bot_token: Secret[str]
    database_uri: Secret[str] = Secret[str](_LOCAL_DATABASE_URI)
    locale: Literal["ru"] = "ru"

    model_config = SettingsConfigDict(env_file=".env", frozen=True)

    @field_validator("database_uri", mode="before")
    @classmethod
    def _db_uri_validator(cls, value: str):
        if value == "LOCAL":
            value = _LOCAL_DATABASE_URI
        return value


app_cfg = AppConfig.model_validate({})


def setup_logging():
    logging.basicConfig(level=logging.INFO)


def create_i18n_middleware():
    return I18nMiddleware(
        core=FluentRuntimeCore(
            path=LOCALES_DIR,
        ),
        manager=I18nMiddlewareManager(),
        default_locale="ru",
    )


@main_router.startup()
async def drop_updates(bots: list[Bot]):
    for bot in bots:
        await bot.delete_webhook(drop_pending_updates=True)
