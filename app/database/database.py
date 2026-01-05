from __future__ import annotations

from abc import ABCMeta
import asyncio
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from aiogram.types import Update, User
from aiogram.dispatcher.event.bases import skip

from app import utils
from app.database.models import UserConfig
from app.database import orm
from app.main import app_cfg, dp


if TYPE_CHECKING:
    from app.handlers.middlewares import MiddlewareData


logger = utils.get_logger()


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
        self.engine = create_async_engine(app_cfg.get_db_uri(mode="async"))
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
            await conn.run_sync(orm.Base.metadata.create_all)

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
                            logger.info(f"saved user {user.id}:{user.full_name}")
                except Exception:
                    logger.exception("Save user error")
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
