from typing import (
    TYPE_CHECKING,
    ClassVar,
    Final,
    Generic,
    Literal,
    TypeVar,
    Self,
    Unpack,
    cast,
    get_args,
)

import datetime
import warnings
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from types import get_original_bases

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_serializer,
    field_validator,
)
from pydantic.warnings import GenericBeforeBaseModelWarning

from aiogram.types import Message

from app import utils
from app.mood import _MoodMonthMixin, Mood, create_days_list, create_days_notes_list

from app._database import orm


warnings.filterwarnings("ignore", category=GenericBeforeBaseModelWarning)


T = TypeVar("T", bound=orm.Base)
logger = utils.get_logger()


class DatabaseMixin(Generic[T], BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    if TYPE_CHECKING:
        __orm_model__: ClassVar[type[T]]  # type: ignore

    def __init_subclass__(cls, **kwargs: Unpack[ConfigDict]):
        super().__init_subclass__(**kwargs)
        orm_type = None
        for type_ in [
            type_ for base in get_original_bases(cls) for type_ in get_args(base)
        ]:
            if issubclass(type_, orm.Base):
                orm_type = type_
                break
        assert orm_type is not None
        cls.__orm_model__ = cast(type[T], orm_type)

    @classmethod
    def from_orm(cls, obj: T) -> Self:
        return cls.model_validate(obj.orm_dump())

    def to_orm(self) -> T:
        return self.__orm_model__.from_model(self)

    async def merge(self):
        from app import main

        async with main.dp["db"].begin() as session:
            return await session.merge(self.to_orm())


class UserConfig(DatabaseMixin[orm.UserConfig]):
    user_id: int
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    locale: str | None = None
    timezone: str | None = None
    gender: Literal["male", "female"] | None = None

    @field_serializer("username")
    def _dump_username(self, value: str | None):
        if value is not None:
            return value.lower()

    @field_validator("timezone")
    @classmethod
    def _validate_timezone(cls, value: str | None):
        if value is not None:
            try:
                ZoneInfo(value)
            except ZoneInfoNotFoundError:
                logger.exception(f"{value=}")
                value = None
        return value

    @property
    def name(self, html: bool = True):
        name = (
            f"{self.first_name or ''} {self.last_name or ''}".strip()
            or self.username
            or str(self.user_id)
        )
        if html:
            name = utils.escape_html(name)
        return name

    @property
    def url(self):
        return (
            f"https://t.me/{self.username}"
            if self.username
            else f"tg://openmessage?user_id={self.user_id}"
        )

    @property
    def text_url(self):
        return f'<a href="{self.url}">{self.name}</a>'

    @property
    def tz(self):
        return ZoneInfo(self.timezone or "Europe/Kyiv")

    @property
    def datetime(self):
        return datetime.datetime.now(self.tz)

    @property
    def lang_code(self) -> str:
        return self.locale or "ru"

    @property
    def sex(self):
        return self.gender or "male"


class MoodMonth(DatabaseMixin[orm.MoodMonth], _MoodMonthMixin):
    user_id: int
    year: int
    month: int
    days: list[Mood] = Field(
        default_factory=lambda data: create_days_list(data["year"], data["month"])
    )
    days_notes: list[str | None] = Field(
        default_factory=lambda data: create_days_notes_list(data["year"], data["month"])
    )

    DAY_NOTE_LIMIT_LENGHT: ClassVar[Final[int]] = 3000

    def get_note(self, day: int):
        return self.days_notes[day - 1]

    def save_note(self, day: int, note: str):
        self.days_notes[day - 1] = note

    def get_mood(self, day: int):
        """:param day: Human-readable day of month"""
        return self.days[day - 1]

    def save_mood(self, day: int, mood: Mood):
        self.days[day - 1] = mood

    async def merge(self):
        from app import main

        orm_obj = await super().merge()

        if any(map(int, self.days)) or any(self.days_notes):
            return orm_obj

        async with main.dp["db"].begin() as session:
            await session.delete(orm_obj)
            return orm_obj

    @field_validator("days_notes", mode="before")
    @classmethod
    def _validate_days_notes(cls, notes: list[str | None] | None, info: ValidationInfo):
        if notes is None:
            notes = create_days_notes_list(info.data["year"], info.data["month"])
        return notes

    @field_validator("days", mode="before")
    @classmethod
    def _validate_days(cls, days: list[int | Mood]):
        for i, mood in enumerate(days):
            if isinstance(mood, int):
                days[i] = list(Mood)[mood]

        return days

    @field_serializer("days")
    def _serialize_days(self, days: list[Mood]):
        return list(map(int, days))

    create_days_list = staticmethod(create_days_list)


class MoodConfig(DatabaseMixin[orm.MoodConfig]):
    user_id: int
    notify_state: bool = False
    notify_chat_id: int | None = None
    notify_chat_topic_id: int | None = None
    notify_time: datetime.time = Field(default_factory=datetime.time)

    def notify_reset(self):
        fields = self.__pydantic_fields__
        data = self.model_dump()
        for field in (
            "notify_state",
            "notify_chat_id",
            "notify_chat_topic_id",
            "notify_time",
        ):
            setattr(
                self,
                field,
                fields[field].get_default(
                    call_default_factory=True, validated_data=data
                ),
            )

    @property
    def notify_time_emoji(self):
        return utils.time_emoji(self.notify_time)

    @property
    def notify_time_str(self):
        return self.notify_time.strftime(r"%H:%M")

    async def merge(self):
        from app.handlers.mood import MoodNotifyConfigurator

        result = await super().merge()
        await utils.suppress_error(MoodNotifyConfigurator.on_change_config(self))
        return result


class UserLastMessage(DatabaseMixin[orm.UserLastMessage]):
    user_id: int
    chat_id: int
    topic_id: Literal[0] | int = 0
    message: Message
