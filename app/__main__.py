from pathlib import Path
from typing import Annotated
import uvloop
import typer

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties

from app import main
from app import handlers
from app.main import dp, setup_logging
from app.config import get_app_config
from app.database import Database
from app.scheduler import Scheduler
from app.geo import Geolocator


def run_app(
    env_file: Annotated[Path | None, typer.Option(help="default: .env")] = None,
    dev: Annotated[bool, typer.Option(is_flag=True, hidden=True)] = False,
):
    main.DEV_MODE = dev

    if main.DEV_MODE and env_file is None:
        env_file = Path(".dev.env")

    app_cfg = dp["app_cfg"] = get_app_config(env_file=env_file)
    bot = dp["main_bot"] = Bot(
        token=app_cfg.bot_token.get_secret_value(),
        default=DefaultBotProperties(
            parse_mode="html",
            allow_sending_without_reply=True,
            disable_notification=True,
            link_preview_is_disabled=True,
        ),
    )

    setup_logging()

    dp["db"] = Database()
    dp["scheduler"] = Scheduler()
    dp["geo"] = Geolocator()

    handlers.register()

    uvloop.run(dp.start_polling(bot))


if __name__ == "__main__":
    typer.run(run_app)
