import pytz

from pydantic import BaseModel, Field, field_serializer, field_validator

from app.mood import _MoodMonthMixin, Mood, create_days_list


class UserConfig(BaseModel):
    user_id: int
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    locale: str | None = None
    timezone: str | None = None
    mood_notify: bool = False

    @field_serializer("username", when_used="json")
    def _dump_username(self, value: str | None):
        if value is not None:
            return value.lower()

    @property
    def tz(self):
        return pytz.timezone(self.timezone or "asia/almaty")

    @property
    def lang_code(self) -> str:
        return self.locale or "ru"


class MoodMonth(BaseModel, _MoodMonthMixin):
    user_id: int
    year: int
    month: int
    days: list[Mood] = Field(
        default_factory=lambda data: create_days_list(data["year"], data["month"])
    )

    model_config = {"from_attributes": True}

    create_days_list = staticmethod(create_days_list)

    def get_mood(self, day: int):
        """:param day: Human-readable day of month"""
        return self.days[day - 1]

    @field_validator("days", mode="before")
    @classmethod
    def _validate_days(cls, days: list[int | Mood]):
        for i, mood in enumerate(days):
            if isinstance(mood, int):
                days[i] = list(Mood)[mood]

        return days

    @field_serializer("days", when_used="json")
    def _serialize_days(self, days: list[Mood]):
        return list(map(int, days))
