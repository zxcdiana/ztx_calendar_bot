import asyncio
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties

from app.database import Database
from app.scheduler import Scheduler

from app.main import app_cfg, dp, setup_logging, create_i18n_middleware

setup_logging()

dp["app_cfg"] = app_cfg
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


@dp.startup()
async def get_loop(dispatcher):
    dispatcher["loop"] = asyncio.get_running_loop()


import app.handlers  # noqa: E402, F401


dp.run_polling(bot)
