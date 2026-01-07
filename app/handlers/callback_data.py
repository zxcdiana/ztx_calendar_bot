from typing import Any, Literal, Self

from aiogram.filters.callback_data import CallbackData as _CallbackData
from aiogram.types import CallbackQuery

from magic_filter import MagicFilter

from app.i18n import I18nContext
from app.config import AppConfig
from app.mood import _MoodMonthMixin
from app.handlers.filters import ctx_and_f


class CallbackData(_CallbackData, prefix="*"):
    def __init_subclass__(cls, **kwargs: Any) -> None:
        if "prefix" not in kwargs:
            kwargs["prefix"] = cls.__name__.lower()

        return super().__init_subclass__(**kwargs)

    @classmethod
    def merge(cls, obj: CallbackData, **args):
        return cls.model_validate(
            {**obj.model_dump(mode="json"), **args}, extra="ignore"
        )


class OwnedCallbackData(CallbackData):
    user_id: int

    @classmethod
    async def _users_filter(
        cls,
        event: CallbackQuery,
        callback_data: Self,
        i18n: I18nContext,
        app_cfg: AppConfig,
    ):
        if (
            callback_data.user_id == event.from_user.id
            or event.from_user.id in app_cfg.owners
        ):
            return True

        await event.answer(i18n.error.button_wrong_user(), cache_time=99999)

    @classmethod
    def filter(cls, rule: MagicFilter | None = None):  # type: ignore
        return ctx_and_f(super().filter(rule), cls._users_filter)


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
    value: int
    go_to: Literal["day", "month"]


empty_callback_data = EmptyCallbackData()
