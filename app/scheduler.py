from __future__ import annotations

import re
from datetime import UTC
from types import CoroutineType
from typing import Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from app.database.database import Singleton
from app.main import dp, app_cfg


def wrap[T](fn: Callable[..., T]) -> Callable[..., CoroutineType[None, None, T]]:
    # apscheduler calling asyncio.get_running_loop()
    async def wrapped():
        return fn()

    return wrapped


class Scheduler(AsyncIOScheduler, metaclass=Singleton):
    def __init__(self):
        super().__init__(timezone=UTC)

        db_url = app_cfg.database_uri.get_secret_value()
        if r := re.fullmatch(r"(.+?)\+(aiosqlite|asyncpg)", db_url.split(":")[0]):
            db_url = r.group(1) + ":" + db_url.split(":", maxsplit=1)[1]

        self.jobstore = SQLAlchemyJobStore(db_url)
        self.add_jobstore(self.jobstore)
        dp.startup.register(wrap(self.start))
        dp.shutdown.register(wrap(self.shutdown))
