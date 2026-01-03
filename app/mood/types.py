import enum
from datetime import date
from pydantic import BaseModel, Field
from dateutil.relativedelta import relativedelta


class Mood(enum.IntEnum):
    UNSET = 0
    AWESOME = 1
    GREET = 2
    GOOD = 3
    OKAY = 4
    BAD = 5
    TERRIBLE = 6


class MoodEmoji(enum.StrEnum):
    UNSET = ""
    AWESOME = "💜"
    GREET = "💙"
    GOOD = "🩵"
    OKAY = "💛"
    BAD = "🧡"
    TERRIBLE = "🤎"


mood_to_str = {
    0: "unset",
    1: "awesome",
    2: "greet",
    3: "good",
    4: "okay",
    5: "bad",
    6: "terrible",
}.__getitem__


def create_days_list(year: int, month: int) -> list[Mood]:
    month_date = date(year, month, 1)
    days = days_in_month(month_date)
    return [Mood.UNSET] * days


def days_in_month(date: date):
    return (date + relativedelta(months=1) - date).days


def date_to_dict(date: date):
    return dict(year=date.year, month=date.month, day=date.day)


class _MoodMonthMixin:
    @property
    def date(self):
        return date(self.year, self.month, getattr(self, "day", 1))  # pyright: ignore[reportAttributeAccessIssue]


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
