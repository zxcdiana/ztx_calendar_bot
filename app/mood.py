import enum
from datetime import date
from dateutil.relativedelta import relativedelta


class _MoodMonthMixin:
    @property
    def date(self):
        return date(self.year, self.month, getattr(self, "day", 1))  # type: ignore


class Mood(enum.Enum):
    UNSET = (0, "")
    AWESOME = (1, "💜")
    GREET = (2, "💙")
    GOOD = (3, "🩵")
    OKAY = (4, "💛")
    BAD = (5, "🧡")
    TERRIBLE = (6, "💀")

    def __init__(self, index: int, emoji: str):
        self.index = index
        self.emoji = emoji

    def __int__(self):
        return self.index

    def __str__(self):
        return self.emoji

    @classmethod
    def convert(cls, value: str | int):
        return [x for x in cls if value in {x.index, x.emoji}][0]


def create_days_list(year: int, month: int) -> list[Mood]:
    month_date = date(year, month, 1)
    days = days_in_month(month_date)
    return [Mood.UNSET] * days


def create_days_notes_list(year: int, month: int) -> list[str | None]:
    return [None] * days_in_month(date(year, month, 1))


def days_in_month(date: date):
    return (date + relativedelta(months=1) - date).days


def date_to_dict(date: date):
    return dict(year=date.year, month=date.month, day=date.day)
