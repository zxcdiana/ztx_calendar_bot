from __future__ import annotations

import asyncio
from pathlib import Path
import logging


from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import SimpleEventIsolation
from aiogram.types import BotCommandScopeDefault, BotCommand
from aiogram.methods import SetMyCommands

from app import utils
from app.config import app_cfg
from app.i18n import FluentRuntimeCore, I18nMiddleware, I18nMiddlewareManager


logger = utils.get_logger()


APP_DIR = Path(__file__).parent.parent
LOCALES_DIR = APP_DIR / "locales/"


dp = Dispatcher(events_isolation=SimpleEventIsolation())
main_router = dp.include_router(Router())
commands_router = main_router.include_router(Router())
mood_router = commands_router.include_router(Router())
admin_router = commands_router.include_router(Router())


dp["app_cfg"] = app_cfg
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


@main_router.startup()
async def set_my_commands(bot: Bot):
    for commands in get_my_commands():
        asyncio.create_task(bot(commands))
