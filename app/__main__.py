from aiogram import Bot
from aiogram.client.default import DefaultBotProperties

from app.config import AppConfig
from app.services import Database, Scheduler
from app.loggers import setup_logging
from app.routers import dp
from app.i18n import create_i18n_middleware


setup_logging()

dp["app_cfg"] = app_cfg = AppConfig.model_validate({})
dp["db"] = Database()
dp["scheduler"] = Scheduler()
create_i18n_middleware().setup(dp)

bot = Bot(
    token=app_cfg.bot_token.get_secret_value(),
    default=DefaultBotProperties(
        parse_mode="html",
        allow_sending_without_reply=True,
        disable_notification=True,
        link_preview_prefer_small_media=True,
    ),
)

import app.handlers  # noqa: E402, F401

dp.run_polling(bot)
