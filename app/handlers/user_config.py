from __future__ import annotations

from typing import Any, Unpack


from aiogram import F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.filters import Command, CommandObject


from app import utils
from app.geo import Geolocator
from app.main import commands_router
from app.i18n import I18nContext
from app.database import Database, UserConfig

from app.handlers.common import Handler
from app.handlers.middlewares import MiddlewareData
from app.handlers.callback_data import (
    UserConfigCallback,
    UserConfigSwitchGender,
)


logger = utils.get_logger()


class UserConfigurator(Handler[Message | CallbackQuery]):
    @classmethod
    def register(cls) -> None:
        return

        commands_router.message.register(cls, Command("me", magic=~F.args))
        commands_router.callback_query.register(cls, UserConfigCallback.filter())

        commands_router.callback_query.register(
            cls.switch_gender_handler, UserConfigSwitchGender.filter()
        )

    @classmethod
    async def switch_gender_handler(
        cls, call: CallbackQuery, **data: Unpack[MiddlewareData]
    ):
        user_config = data["user_config"]
        if user_config.sex == "male":
            gender = "female"
        else:
            gender = "male"
        user_config.gender = gender
        await user_config.merge()
        panel = await cls.main_panel(data)
        await call.message.edit_text(**panel)  # type: ignore
        await utils.suppress_error(call.answer(data["i18n"].gender.changed()))

    @classmethod
    async def main_panel(cls, data: MiddlewareData) -> dict[str, Any]:
        i18n = data["i18n"]
        user_config = data["user_config"]
        text = "\xad"
        kb = [
            [
                InlineKeyboardButton(
                    text=i18n.get(f"gender-{user_config.sex}_button"),
                    callback_data=UserConfigSwitchGender(
                        user_id=user_config.user_id
                    ).pack(),
                )
            ]
        ]
        return dict(text=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

    async def handle(self):
        m, call = utils.split_event(self.event)
        panel = await self.main_panel(self.data)
        if call:
            await m.edit_text(**panel)
        elif m.chat.type == "private":
            await m.answer(**panel)
        else:
            await m.reply(**panel)


@commands_router.message(
    Command("tz", magic=~F.args | F.args.len() <= 30), F.text.splitlines().len() <= 3
)
async def set_timezone(
    m: Message,
    command: CommandObject,
    geo: Geolocator,
    db: Database,
    user_config: UserConfig,
    i18n: I18nContext,
):
    from app.handlers.mood import MoodNotifyConfigurator

    answer = m.answer if m.chat.type == "private" else m.reply
    date_time_fmt = r"%H:%M, %d.%m.%y ({})"

    if command.args is None:
        await answer(
            text=i18n.tz_command.info(
                time_emoji=utils.time_emoji(user_config.datetime),
                date_time=user_config.datetime.strftime(
                    date_time_fmt.format(utils.utc_offset(user_config.datetime))
                ),
                command=command.text,
            )
            # TODO inline query set timezone button
        )
        return

    loading = await answer(text=i18n.loading())

    try:
        timezone = await geo.get_timezone(command.args)
    except Exception:
        logger.exception(f"query={command.args}")
        timezone = None

    if timezone is None:
        await loading.edit_text(
            text=i18n.tz_command.timezone404(
                query=geo.normalize_query(command.args) or ""
            )
            or ""
        )
        return

    user_config.timezone = timezone
    await user_config.merge()
    await MoodNotifyConfigurator.on_change_config(
        await db.get_mood_config(user_config.user_id)
    )

    await loading.edit_text(
        text=i18n.tz_command.changed(
            time_emoji=utils.time_emoji(user_config.datetime),
            date_time=user_config.datetime.strftime(
                date_time_fmt.format(utils.utc_offset(user_config.datetime))
            ),
        )
    )
