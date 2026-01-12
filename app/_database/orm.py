from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any, ClassVar, Self

import sqlalchemy as sa
from sqlalchemy import JSON, BigInteger, Integer, String, Time, ARRAY, Text
from sqlalchemy.orm import Mapped, mapped_column as column
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy_utc import UtcDateTime, utcnow


if TYPE_CHECKING:
    from pydantic import BaseModel


class Base(DeclarativeBase, AsyncAttrs):
    created_at: Mapped[datetime.datetime] = column(
        UtcDateTime(), server_default=utcnow(), autoincrement=True
    )
    updated_at: Mapped[datetime.datetime] = column(
        UtcDateTime(), server_default=utcnow(), onupdate=utcnow(), autoincrement=True
    )

    if TYPE_CHECKING:
        columns: ClassVar[set[str]]

    def __init_subclass__(cls, table: str, **kw):
        cls.__tablename__ = table
        super().__init_subclass__(**kw)
        cls.columns = set(map(lambda x: x.name, sa.inspect(cls).columns))

    def orm_dump(self):
        exclude = "created_at", "updated_at"
        return {k: getattr(self, k) for k in self.columns if k not in exclude}

    @classmethod
    def from_model(cls, obj: BaseModel) -> Self:
        data = obj.model_dump(include=cls.columns, exclude_none=True)
        return cls(**data)


class MoodMonth(Base, table="mood"):
    user_id: Mapped[int] = column(BigInteger, primary_key=True)
    year: Mapped[int] = column(Integer, primary_key=True)
    month: Mapped[int] = column(Integer, primary_key=True)
    days: Mapped[list[int]] = column(JSON, nullable=False)
    days_notes: Mapped[list[str] | None] = column(ARRAY(Text))


class UserConfig(Base, table="users"):
    user_id: Mapped[int] = column(BigInteger, primary_key=True)
    first_name: Mapped[str | None] = column(String(64), nullable=True)
    last_name: Mapped[str | None] = column(String(64), nullable=True)
    username: Mapped[str | None] = column(String(32), nullable=True, unique=True)
    locale: Mapped[str | None] = column(String(2), nullable=True)
    timezone: Mapped[str | None] = column(String(64), nullable=True)
    gender: Mapped[str | None] = column(String(6), nullable=True)


class MoodConfig(Base, table="mood_config"):
    user_id: Mapped[int] = column(BigInteger, primary_key=True)
    notify_state: Mapped[bool] = column(server_default=sa.text("false"))
    notify_chat_id: Mapped[int | None] = column(BigInteger, nullable=True)
    notify_chat_topic_id: Mapped[int | None] = column(BigInteger, nullable=True)
    notify_time: Mapped[datetime.time] = column(Time, server_default=sa.text("'00:00'"))


class UserLastMessage(Base, table="user_last_message"):
    user_id: Mapped[int] = column(BigInteger, primary_key=True)
    chat_id: Mapped[int] = column(BigInteger, primary_key=True)
    topic_id: Mapped[int] = column(
        BigInteger, primary_key=True, server_default=sa.text("0")
    )
    message: Mapped[dict[str, Any]] = column(JSON)
