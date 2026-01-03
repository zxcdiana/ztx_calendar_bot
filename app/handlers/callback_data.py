from typing import Any, Literal
from aiogram.filters.callback_data import CallbackData as _CallbackData

from app.mood.types import _MoodMonthMixin, Mood


class CallbackData(_CallbackData, prefix="*"):
    def __init_subclass__(cls, **kwargs: Any) -> None:
        if "prefix" not in kwargs:
            kwargs["prefix"] = cls.__name__.lower()

        return super().__init_subclass__(**kwargs)

    @classmethod
    def merge(cls, obj: CallbackData, **args):
        return cls.model_validate({**obj.model_dump(), **args}, extra="ignore")


class OwnedCallbackData(CallbackData):
    user_id: int


class EmptyCallbackData(CallbackData):
    pass


class DeleteMessage(OwnedCallbackData):
    pass


class MoodMonthCallback(OwnedCallbackData, _MoodMonthMixin):
    year: int
    month: int
    marker: int = -1
    alert_marker: bool = False
    """`-1`: disable, `0-6`: mark day"""


class OpenMoodDay(MoodMonthCallback, _MoodMonthMixin):
    day: int


class MarkMoodDay(OpenMoodDay):
    value: Mood
    go_to: Literal["day", "month"]


empty_callback_data = EmptyCallbackData()
