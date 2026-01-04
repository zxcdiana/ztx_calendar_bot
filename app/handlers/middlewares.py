from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiogram import BaseMiddleware
from aiogram.dispatcher.middlewares.data import MiddlewareData as _MiddlewareData
import uvloop

from app import utils
from app.main import AppConfig, dp, main_router
from app.database.database import Singleton

if TYPE_CHECKING:
    from app.i18n import I18nContext, I18nMiddleware
    from app.database import Database, UserConfig
    from app.scheduler import Scheduler

logger = utils.get_logger()


class MiddlewareData(_MiddlewareData):
    app_cfg: AppConfig
    user_config: UserConfig
    db: Database
    scheduler: Scheduler
    i18n_middleware: I18nMiddleware
    i18n: I18nContext
    callback_data: Any
    command: Any
    loop: uvloop.Loop


class AntiFlood(BaseMiddleware, metaclass=Singleton):
    MESSAGE_THRESHOLD = 0.500

    def __init__(self):
        self.users: dict[int, float] = {}

    async def __call__(self, handler, event, data: MiddlewareData):  # type: ignore
        event_context = data.get("event_context")
        loop = data["loop"]
        user_id = getattr(event_context, "user_id", None) or -1
        is_from_admin = user_id in data["app_cfg"].owners
        last_time = self.users.get(user_id) or 0

        if not is_from_admin and (last_time + self.MESSAGE_THRESHOLD > loop.time()):
            logger.info(f"Got flood from {user_id}, event skipped")
            self.users[user_id] = loop.time() + self.MESSAGE_THRESHOLD
            return
        try:
            return await handler(event, data)  # type: ignore
        finally:
            self.users[user_id] = loop.time()


anti_flood_mw = dp["anti_flood_mw"] = AntiFlood()
main_router.message.middleware.register(anti_flood_mw)
