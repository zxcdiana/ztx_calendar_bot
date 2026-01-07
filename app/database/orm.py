from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import JSON, BigInteger, Integer, String, inspect, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs

if TYPE_CHECKING:
    from pydantic import BaseModel


class Base(DeclarativeBase, AsyncAttrs):
    def __init_subclass__(cls, table: str, **kw):
        cls.__tablename__ = table
        return super().__init_subclass__(**kw)

    @classmethod
    def from_model(cls, obj: BaseModel):
        data = obj.model_dump(mode="json")
        return cls(**{k: data[k] for k in map(lambda x: x.name, inspect(cls).columns)})


class MoodMonth(Base, table="mood"):
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    month: Mapped[int] = mapped_column(Integer, primary_key=True)
    days: Mapped[list[int]] = mapped_column(JSON, nullable=False)


class UserConfig(Base, table="users"):
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    first_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    username: Mapped[str | None] = mapped_column(String(32), nullable=True, unique=True)
    locale: Mapped[str | None] = mapped_column(String(2), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mood_notify: Mapped[bool] = mapped_column(server_default=text("false"))
