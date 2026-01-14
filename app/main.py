# pyright: reportIncompatibleMethodOverride=false

from __future__ import annotations

import asyncio
from pathlib import Path
import logging
from typing import TYPE_CHECKING, Any, Literal, overload


import aiogram
from aiogram import Bot, Router
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import SimpleEventIsolation
from aiogram.types import BotCommandScopeDefault, BotCommand
from aiogram.methods import SetMyCommands
from telethon import TelegramClient

from app import utils
from app.geo import asynccontextmanager
from app.i18n import FluentRuntimeCore, I18nMiddleware, I18nMiddlewareManager
from app.telethon_session import AsyncSQLiteSession


logger = utils.get_logger()


APP_DIR = Path(__file__).parent.parent
LOCALES_DIR = APP_DIR / "locales/"

DEV_MODE: bool

# fmt: off
if TYPE_CHECKING:
    from app.config import AppConfig
    from app.meta import AppMetadata
    from app.i18n import I18nMiddleware
    from app.database import Database
    from app.scheduler import Scheduler
    from app.geo import Geolocator
    from app.handlers.middlewares import AntiFlood
    from uvloop import Loop

    class Dispatcher(aiogram.Dispatcher):
        @overload
        def __getitem__(self, key: Literal['app_cfg']) -> AppConfig: ...
        @overload
        def __getitem__(self, key: Literal['app_metadata']) -> AppMetadata: ...
        @overload
        def __getitem__(self, key: Literal['main_bot']) -> Bot: ...
        @overload
        def __getitem__(self, key: Literal['i18n_middleware']) -> I18nMiddleware: ...
        @overload
        def __getitem__(self, key: Literal['db']) -> Database: ...
        @overload
        def __getitem__(self, key: Literal['scheduler']) -> Scheduler: ...
        @overload
        def __getitem__(self, key: Literal['geo']) -> Geolocator: ...
        @overload
        def __getitem__(self, key: Literal['anti_flood_mw']) -> AntiFlood: ...
        @overload
        def __getitem__(self, key: Literal['loop']) -> Loop: ...
        def __getitem__(self, key: Any) -> Any: ...
        @overload
        def get(self, key: Literal['tl_bot']) -> TelegramClient: ...
        @overload
        def get(self, key: Any) -> Any: ...
        def get(self, key: Any) -> Any: ...
else:
    Dispatcher = aiogram.Dispatcher
# fmt: on


class ConcurrentEventError(Exception):
    pass


class EventIsolation(SimpleEventIsolation):
    @asynccontextmanager
    async def lock(self, key: StorageKey):
        lock = self._locks[key]
        if lock.locked():
            raise ConcurrentEventError()
        async with lock:
            yield


dp = Dispatcher(events_isolation=EventIsolation())
main_router = dp.include_router(Router())
commands_router = main_router.include_router(Router())
mood_router = commands_router.include_router(Router())
admin_router = commands_router.include_router(Router())
last_router = main_router.include_router(Router())


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
                    for cmd in ["start", "mood", "notify", "tz", "version"]
                ],
            )
        )

    return result


def get_owner_commands() -> list[BotCommand]:
    i18n: I18nMiddleware = dp["i18n_middleware"]
    return [
        BotCommand(command=cmd, description=i18n.core.get(f"bot_command-{cmd}"))
        for cmd in ("eval",)
    ]


@dp.startup()
async def get_loop(dispatcher):
    dispatcher["loop"] = asyncio.get_running_loop()


@main_router.startup()
async def set_my_commands(bot: Bot):
    for commands in get_my_commands():
        asyncio.create_task(bot(commands))


@dp.startup()
async def create_telethon_client(dispatcher: Dispatcher, app_cfg: AppConfig):
    if app_cfg.api_id is None or app_cfg.api_hash is None:
        return
    client = TelegramClient(
        AsyncSQLiteSession(
            f"bot_{app_cfg.bot_token.get_secret_value().split(':')[0]}.session"
        ),
        api_id=app_cfg.api_id.get_secret_value(),
        api_hash=app_cfg.api_hash.get_secret_value(),
    )
    try:
        async with asyncio.timeout(30):
            await client.start(  # type: ignore
                bot_token=app_cfg.bot_token.get_secret_value()
            )
            assert await client.get_me()
    except Exception:
        await utils.suppress_error(client.disconnect())  # type: ignore
        logger.exception("telethon client not loaded")
        return
    else:
        dispatcher["tl_bot"] = client


@dp.update.outer_middleware
async def suppress_concurrent_event_error(handler, event, data):
    try:
        return await handler(event, data)
    except ConcurrentEventError:
        pass


dp.update.outer_middleware._middlewares.insert(
    0, dp.update.outer_middleware._middlewares.pop(-1)
)
