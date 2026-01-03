from __future__ import annotations

from abc import ABCMeta
import asyncio
from contextlib import asynccontextmanager
import re
from datetime import UTC
from typing import TYPE_CHECKING

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from aiogram.types import Update, User
from aiogram.dispatcher.event.bases import skip
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from app import loggers, orm
from app.routers import dp
from app.config import app_cfg
from app.orm import Base
from app.types import UserConfig

if TYPE_CHECKING:
    from app.handlers.middlewares import MiddlewareData


class Singleton(ABCMeta):
    def __new__(mcls, name, bases, namespace, /, **kwargs):
        cls = super().__new__(mcls, name, bases, namespace, **kwargs)
        raw_init = cls.__init__
        is_initialized = False

        def __init_wrapper__(*a, **kw):
            nonlocal is_initialized
            if is_initialized:
                raise RuntimeError("Singleton already initialized")
            is_initialized = True
            return raw_init(*a, **kw)

        cls.__init__ = __init_wrapper__
        return cls


class Cache(metaclass=Singleton):
    users: dict[int, UserConfig] = {}
    locks: dict[str, asyncio.Lock] = {"save_users_lock": asyncio.Lock()}


class Database(metaclass=Singleton):
    def __init__(self) -> None:
        self.engine = create_async_engine(app_cfg.database_uri.get_secret_value())
        self.sessionmaker = async_sessionmaker(self.engine)
        self.cache = Cache()

        dp.startup.register(self.startup)
        dp.update.outer_middleware.register(self.outer_middleware)  # pyright: ignore[reportArgumentType]
        dp.update.register(self.save_user_handler)

        registered = dp.update.handlers[-1]
        dp.update.handlers.pop(-1)
        dp.update.handlers.insert(0, registered)

    async def startup(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    def extract_users(self, event: BaseModel) -> list[User]:
        users: list[User] = []
        fields = list(event.model_dump())

        for value in map(lambda x: getattr(event, x), fields):
            if isinstance(value, User):
                users += [value]
            elif isinstance(value, BaseModel):
                users += self.extract_users(value)

        return users

    @asynccontextmanager
    async def begin(self):
        async with self.sessionmaker() as session, session.begin():
            yield session

    async def get_user(self, user_id: int) -> UserConfig:
        if user_id in self.cache.users:
            return self.cache.users[user_id]

        lock_key = f"user:{user_id}"
        if lock_key not in self.cache.locks:
            self.cache.locks[lock_key] = asyncio.Lock()

        async with self.cache.locks[lock_key], self.sessionmaker() as session:
            stmt = select(orm.UserConfig).where(orm.UserConfig.user_id == user_id)
            if orm_user := await session.scalar(stmt):
                user_config = UserConfig.model_validate(orm_user, from_attributes=True)
            else:
                user_config = UserConfig(user_id=user_id)
            self.cache.users[user_id] = user_config
            self.cache.locks.pop(lock_key, None)

        return self.cache.users[user_id]

    async def save_user_handler(self, update: Update):
        async def handler(self: Database, update: Update):
            async with self.cache.locks["save_users_lock"]:
                try:
                    users = self.extract_users(update.event)
                    if not users:
                        return

                    async with self.begin() as session:
                        for user in users:
                            user_config = await self.get_user(user.id)
                            user_config.first_name = user.first_name
                            user_config.last_name = user.last_name
                            user_config.username = user.username
                            await session.merge(orm.UserConfig.from_model(user_config))
                            loggers.database.info(
                                f"saved user {user.id}:{user.full_name}"
                            )
                except Exception:
                    loggers.database.exception("Save user error")
                finally:
                    await asyncio.sleep(0.5)

        task = asyncio.create_task(handler(self, update))
        dp._handle_update_tasks.add(task)
        task.add_done_callback(dp._handle_update_tasks.discard)
        skip()

    async def outer_middleware(self, handler, event, data: MiddlewareData):
        ctx = data.get("event_context")
        if ctx and ctx.user_id:
            data["user_config"] = await self.get_user(ctx.user_id)
        return await handler(event, data)

    async def save(self, obj: UserConfig | UserConfig):
        if isinstance(obj, UserConfig):
            if obj is not self.cache.users.get(obj.user_id):
                self.cache.users[obj.user_id] = obj
        else:
            raise

        async with self.begin() as session:
            await session.merge(orm.UserConfig.from_model(obj))


def wrap(fn):
    async def _():
        return fn()

    return _


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
