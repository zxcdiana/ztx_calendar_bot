from typing import Any
from aiogram.dispatcher.middlewares.data import MiddlewareData as _MiddlewareData

from app.i18n import I18nContext, I18nMiddleware
from app.services import Database, Scheduler
from app.types import UserConfig


class MiddlewareData(_MiddlewareData):
    user_config: UserConfig
    db: Database
    scheduler: Scheduler
    i18n_middleware: I18nMiddleware
    i18n: I18nContext
    callback_data: Any
    command: Any
