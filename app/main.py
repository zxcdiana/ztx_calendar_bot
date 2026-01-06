from __future__ import annotations

import asyncio
import re
from typing import Literal
from pathlib import Path
import platformdirs
import logging

from pydantic import Secret, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import SimpleEventIsolation
from aiogram.types import BotCommandScopeDefault, BotCommand
from aiogram.methods import SetMyCommands

from app.i18n import FluentRuntimeCore, I18nMiddleware, I18nMiddlewareManager


APP_DIR = Path(__file__).parent.parent
CONFIG_DIR = platformdirs.user_config_path("ztx_calendar_bot", ensure_exists=True)
DATABASE_PATH = CONFIG_DIR / "database.sqlite3"
LOCALES_DIR = APP_DIR / "locales/"


dp = Dispatcher(events_isolation=SimpleEventIsolation())
main_router = dp.include_router(Router())
commands_router = main_router.include_router(Router())
mood_router = commands_router.include_router(Router())
admin_router = commands_router.include_router(Router())


class AppConfig(BaseSettings):
    owners: set[int]
    bot_token: Secret[str]
    postgres_uri: Secret[str]
    locale: Literal["ru"] = "ru"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", frozen=True)

    @field_validator("postgres_uri", mode="after")
    @classmethod
    def _postgres_uri_validator(cls, value: Secret[str]):
        if not re.fullmatch(
            r"postgres(ql|)://(?P<user>.+?):(?P<password>.+?)@(?P<host>.+?)/(?P<db>.+?)",
            value.get_secret_value(),
        ):
            raise ValueError(
                "Invalid `postgres_uri`."
                "Value has been in format: `postgresql://<USER>:<PASSWORD>@<HOST>/<DATABASE>`"
            )
        return value

    def get_db_uri(self, /, mode: Literal["sync", "async"]):
        uri = self.postgres_uri.get_secret_value()
        uri = uri[len(re.match(r"postgres(ql|)://", uri)[0]) :]  # pyright: ignore[reportOptionalSubscript]
        if mode == "sync":
            return f"postgresql+psycopg2://{uri}"
        elif mode == "async":
            return f"postgresql+asyncpg://{uri}"
        else:
            raise ValueError(f"invalid mode: {mode}")


app_cfg = dp["app_cfg"] = AppConfig.model_validate({})
bot = Bot(
    token=app_cfg.bot_token.get_secret_value(),
    default=DefaultBotProperties(
        parse_mode="html",
        allow_sending_without_reply=True,
        disable_notification=True,
        link_preview_prefer_small_media=True,
    ),
)


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


create_i18n_middleware().setup(dp)


def get_my_commands() -> list[SetMyCommands]:
    i18n: I18nMiddleware = dp["i18n_middleware"]
    core = i18n.core
    result = []

    for language_code in core.locales:
        result.append(
            SetMyCommands(
                scope=BotCommandScopeDefault(),
                language_code=language_code,
                commands=[
                    BotCommand(
                        command=cmd,
                        description=core.get(f"bot_command-{cmd}", language_code),
                    )
                    for cmd in ["mood"]
                ],
            )
        )

    return result


@dp.startup()
async def get_loop(dispatcher):
    dispatcher["loop"] = asyncio.get_running_loop()


@dp.startup()
async def drop_updates(bots: list[Bot]):
    for bot in bots:
        await bot.delete_webhook(drop_pending_updates=True)


@main_router.startup()
async def set_my_commands(bot: Bot):
    for commands in get_my_commands():
        asyncio.create_task(bot(commands))
