from __future__ import annotations

from typing import TYPE_CHECKING, Iterable
import asyncio
import itertools
from abc import ABCMeta
from collections import defaultdict
from contextlib import asynccontextmanager

from pydantic import BaseModel

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from aiogram import Bot
from aiogram.methods import GetUpdates
from aiogram.types import Message, Update, User
from aiogram.dispatcher.event.bases import skip

from app import utils
from app.main import dp

from app._database import orm
from app._database.models import MoodConfig, MoodMonth, UserConfig, UserLastMessage


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
                raise RuntimeError(f"{cls.__name__} already initialized")
            is_initialized = True
            return raw_init(*a, **kw)

        cls.__init__ = __init_wrapper__
        return cls


class Cache(metaclass=Singleton):
    users: dict[int, UserConfig] = {}
    locks: defaultdict[str, asyncio.Lock] = defaultdict(asyncio.Lock)


class Database(metaclass=Singleton):
    def __init__(self) -> None:
        self.engine = create_async_engine(dp["app_cfg"].get_db_uri(mode="async"))
        self.sessionmaker = async_sessionmaker(self.engine)
        self.cache = Cache()

        dp.startup.register(self.startup)
        dp.startup.register(self.handle_offline_updates)
        dp.update.outer_middleware.register(self.outer_middleware)  # pyright: ignore[reportArgumentType]
        dp.update.register(self.save_users_handler)
        dp.message.register(self.save_last_message_handler)

        # force update handler priority
        registered = dp.update.handlers[-1]
        dp.update.handlers.pop(-1)
        dp.update.handlers.insert(0, registered)

    async def startup(self):
        logger.info("Connecting to database ...")
        try:
            async with self.engine.begin():
                pass
        except Exception:
            logger.exception("Connecting to database failed\n\n---")
            raise
        logger.info("Connected to database")

    async def get_last_message(
        self, chat_id: int, *, user_id: int, topic_id: int | None = None
    ):
        if topic_id is None:
            topic_id = 0

        async with self() as session:
            stmt = (
                sa.select(orm.UserLastMessage)
                .where(orm.UserLastMessage.chat_id == chat_id)
                .where(orm.UserLastMessage.user_id == user_id)
                .where(orm.UserLastMessage.topic_id == topic_id)
            )
            if obj := await session.scalar(stmt):
                return UserLastMessage.from_orm(obj)

    async def save_last_message_handler(self, m: Message):
        task = asyncio.create_task(self.save_last_message(m))
        dp._handle_update_tasks.add(task)
        task.add_done_callback(dp._handle_update_tasks.discard)
        skip()

    async def save_last_message(self, m: Message):
        user = m.from_user
        if user is None or m.chat.type == "private":
            return

        last_message = UserLastMessage(
            user_id=user.id,
            chat_id=m.chat.id,
            topic_id=m.message_thread_id or 0,
            message=m,
        )
        await last_message.merge()

    async def handle_offline_updates(self, bots: list[Bot], db: Database):
        from app import main

        if main.DEV_MODE:
            return
        try:
            async with asyncio.timeout(15):
                await self._handle_offline_updates(bots, db)
        except Exception:
            logger.exception("Error while handle offline updates")

        for bot in bots:
            await bot.delete_webhook(drop_pending_updates=True)

    async def _handle_offline_updates(self, bots: list[Bot], db: Database):
        offline_updates: list[Update] = []

        for bot in bots:
            req = GetUpdates()
            while True:
                updates = await bot(req)
                offline_updates += updates
                if not updates:
                    break
                if len(updates) < 100:
                    break

                req.offset = offline_updates[-1].update_id + 1

        if offline_updates:
            await db.save_users(offline_updates)
            logger.info(f"Handled {len(offline_updates)} offline updates")
        else:
            logger.info("No offline updates")

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
        async with self() as session, session.begin():
            yield session

    @asynccontextmanager
    async def __call__(self, **local_kw):
        async with self.sessionmaker(**local_kw) as session:
            yield session

    async def get_user(self, user_id: int) -> UserConfig:
        if user_id in self.cache.users:
            return self.cache.users[user_id]

        lock_key = f"user:{user_id}"
        async with self.cache.locks[lock_key], self.sessionmaker() as session:
            stmt = sa.select(orm.UserConfig).where(orm.UserConfig.user_id == user_id)
            if orm_user := await session.scalar(stmt):
                user_config = UserConfig.model_validate(orm_user, from_attributes=True)
            else:
                user_config = UserConfig(user_id=user_id)
            self.cache.users[user_id] = user_config

        return self.cache.users[user_id]

    async def get_mood_month(self, user_id: int, *, year: int, month: int):
        async with self() as session:
            stmt = (
                sa.select(orm.MoodMonth)
                .where(orm.MoodMonth.user_id == user_id)
                .where(orm.MoodMonth.year == year)
                .where(orm.MoodMonth.month == month)
            )
            if mood_month_orm := await session.scalar(stmt):
                return MoodMonth.from_orm(mood_month_orm)

            mood_month = MoodMonth(
                user_id=user_id,
                year=year,
                month=month,
            )
            return mood_month

    async def get_mood_config(self, user_id: int):
        async with self() as session:
            stmt = sa.select(orm.MoodConfig).where(orm.MoodConfig.user_id == user_id)
            if cfg := await session.scalar(stmt):
                return MoodConfig.from_orm(cfg)

            return MoodConfig(user_id=user_id)

    async def save_users(self, events: Iterable[BaseModel] | BaseModel):
        async with self.cache.locks["save_users_lock"]:
            if isinstance(events, BaseModel):
                events = (events,)

            users = list(itertools.chain(*map(self.extract_users, events)))
            if not users:
                return
            try:
                async with self.begin() as session:
                    for user in users:
                        user_config = await self.get_user(user.id)
                        user_config.first_name = user.first_name
                        user_config.last_name = user.last_name
                        user_config.username = user.username
                        await session.merge(user_config.to_orm())
            except Exception:
                logger.exception("Save users error")

    async def save_users_handler(self, update: Update):
        task = asyncio.create_task(self.save_users(update))
        dp._handle_update_tasks.add(task)
        task.add_done_callback(dp._handle_update_tasks.discard)
        skip()

    async def outer_middleware(self, handler, event, data: MiddlewareData):
        ctx = data.get("event_context")
        if ctx and ctx.user_id:
            data["user_config"] = await self.get_user(ctx.user_id)
        return await handler(event, data)
