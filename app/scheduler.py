from __future__ import annotations

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

        self.jobstore = SQLAlchemyJobStore(app_cfg.get_db_uri(mode="sync"))
        self.add_jobstore(self.jobstore)
        dp.startup.register(wrap(self.start))
        dp.shutdown.register(wrap(self.shutdown))
