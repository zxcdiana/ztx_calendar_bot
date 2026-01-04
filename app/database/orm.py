from pydantic import BaseModel
from sqlalchemy import JSON, TEXT, inspect
from sqlalchemy.orm import Mapped, mapped_column

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs


class Base(DeclarativeBase, AsyncAttrs):
    def __init_subclass__(cls, table: str, **kw):
        cls.__tablename__ = table
        return super().__init_subclass__(**kw)

    @classmethod
    def from_model(cls, obj: BaseModel):
        data = obj.model_dump(mode="json")
        return cls(**{k: data[k] for k in map(lambda x: x.name, inspect(cls).columns)})


class MoodMonth(Base, table="mood"):
    user_id: Mapped[int] = mapped_column(primary_key=True)
    year: Mapped[int] = mapped_column(primary_key=True)
    month: Mapped[int] = mapped_column(primary_key=True)
    days: Mapped[list[int]] = mapped_column(JSON, nullable=False)


class UserConfig(Base, table="users"):
    user_id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    last_name: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    username: Mapped[str | None] = mapped_column(TEXT, nullable=True, unique=True)
    locale: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    timezone: Mapped[str | None] = mapped_column(TEXT, nullable=True)
