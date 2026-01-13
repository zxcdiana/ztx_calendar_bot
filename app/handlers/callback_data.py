from typing import Any, Literal, Self

from aiogram.filters.callback_data import CallbackData as _CallbackData
from aiogram.types import CallbackQuery, InlineKeyboardButton

from magic_filter import MagicFilter

from app.i18n import I18nContext
from app.config import AppConfig
from app.mood import _MoodMonthMixin
from app.handlers.filters import ctx_and_f


class CallbackData(_CallbackData, prefix="*"):
    def __init_subclass__(cls, **kwargs: Any) -> None:
        if "prefix" not in kwargs:
            kwargs["prefix"] = "".join(
                filter(lambda x: x not in "aeiou", cls.__name__.lower())
            )

        return super().__init_subclass__(**kwargs)

    @classmethod
    def merge(cls, obj: CallbackData, **args):
        return cls.model_validate({**obj.model_dump(), **args}, extra="ignore")

    def update(self, **args):
        return self.model_validate({**self.model_dump(), **args}, extra="ignore")


class OwnedCallbackData(CallbackData, prefix="*"):
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
        return ctx_and_f(super().filter(rule=rule), cls._users_filter)


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


class OpenMoodDay(MoodMonthCallback):
    day: int


class MarkMoodDay(OpenMoodDay):
    value: int
    go_to: Literal["day", "month", "from_notify"]


class MoodDayNote(OpenMoodDay):
    action: Literal["edit", "extend", "delete-warning", "delete"]


class MoodNotifySetTime(OwnedCallbackData, sep="|"):
    time: str
    """`00:00`"""


class MoodNotifySwitchState(OwnedCallbackData):
    pass


class MoodNotifySetChat(OwnedCallbackData):
    chat_id: int | None = None


class MoodNotifyChoiceTime(OwnedCallbackData):
    pass


class UserConfigCallback(OwnedCallbackData):
    pass


class UserConfigSwitchGender(UserConfigCallback):
    pass


empty_callback_data = EmptyCallbackData()


def empty_button(text: str = "\xad"):
    return InlineKeyboardButton(text=text, callback_data=empty_callback_data.pack())
