from __future__ import annotations

import asyncio
import math
import datetime
import re
from typing import Any, Literal, TypedDict, Unpack, cast
from contextlib import asynccontextmanager, suppress
from collections import defaultdict
from dateutil.relativedelta import relativedelta

from apscheduler.jobstores.base import JobLookupError

from aiogram import F, Router, flags
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    TelegramObject,
    ReplyParameters,
)
from aiogram.filters import or_f, Command, StateFilter, MagicData
from aiogram.fsm.state import default_state
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramAPIError
from aiogram.methods import SendMessage

from pydantic import BaseModel, field_validator

from app import utils
from app import main
from app.main import dp, mood_router
from app.mood import Mood, date_to_dict
from app.i18n import I18nContext
from app.database import MoodConfig, UserConfig

from app.handlers.common import Handler
from app.handlers.middlewares import MiddlewareData
from app.handlers.state import input_state
from app.handlers.callback_data import (
    DeleteMessage,
    MarkMoodDay,
    MoodDayNote,
    MoodNotifyChoiceTime,
    MoodNotifySetChat,
    MoodNotifySetTime,
    MoodNotifySwitchDayType,
    MoodNotifySwitchState,
    OpenMoodDay,
    MoodMonthCallback,
    OwnedCallbackData,
    empty_callback_data,
)


logger = utils.get_logger()


class MoodMonthHandler(Handler[Message | CallbackQuery]):
    @classmethod
    def register(cls) -> None:
        mood_router.message.register(
            cls,
            or_f(Command("mood", magic=~F.args), F.text.lower() == "муд"),
        )
        mood_router.callback_query.register(cls, MoodMonthCallback.filter())

    # @classmethod
    # async def middleware(cls, handler, event, data: MiddlewareData):

    @staticmethod
    def str_month(i18n: I18nContext, *, month: int):
        return i18n.get(f"month_{month}")

    @classmethod
    async def panel(cls, data: MiddlewareData):
        cd = data["callback_data"]
        assert isinstance(cd, MoodMonthCallback)
        mood_month = await data["db"].get_mood_month(
            cd.user_id, year=cd.year, month=cd.month
        )
        mark = cd.marker
        text = data["i18n"].mood_month(
            year=str(cd.year),
            month=cls.str_month(data["i18n"], month=cd.month),
            current_dmy=data["user_config"].current_time.strftime(r"%d.%m.%y"),
        )
        kb: list[list[InlineKeyboardButton]] = [
            *utils.chunks(
                (
                    InlineKeyboardButton(
                        text=f"{day}. {mood.emoji}"
                        if mood is not Mood.UNSET
                        else str(day),
                        callback_data=(
                            OpenMoodDay.merge(cd, day=day)
                            if mark == -1
                            else MarkMoodDay.merge(
                                cd, day=day, value=mark, go_to="month"
                            )
                        ).pack(),
                    )
                    for day, mood in enumerate(mood_month.days, 1)
                ),
                5,
            ),
        ]
        filler = [
            InlineKeyboardButton(text="\xad", callback_data=empty_callback_data.pack())
        ]
        i_mn = 0
        for i in range(math.ceil(31 / 5)):
            i += i_mn
            if len(kb) - 1 < i:
                i_mn += 1
                kb += [[]]
            kb[i] += filler * (5 - len(kb[i]))

        row = []
        workflow_date = cd.date
        workflow_date -= relativedelta(months=1)
        row += [
            InlineKeyboardButton(
                text=f"« {cls.str_month(data['i18n'], month=workflow_date.month).lower()[:3:]}",
                callback_data=MoodMonthCallback.merge(
                    cd, year=workflow_date.year, month=workflow_date.month
                ).pack(),
            )
        ]

        next_mark = mark + 1
        if next_mark > len(Mood) - 1:
            next_mark = -1

        row += [
            InlineKeyboardButton(
                text="✏️" + ["🗑", *map(str, list(Mood)[1:]), ""][mark],
                callback_data=MoodMonthCallback.merge(
                    cd, mark=next_mark, alert_marker=True
                ).pack(),
            )
        ]

        workflow_date += relativedelta(months=2)
        row += [
            InlineKeyboardButton(
                text=f"{cls.str_month(data['i18n'], month=workflow_date.month).lower()[:3:]} »",
                callback_data=MoodMonthCallback.merge(
                    cd, year=workflow_date.year, month=workflow_date.month
                ).pack(),
            )
        ]
        kb += [row]
        return {"text": text, "reply_markup": InlineKeyboardMarkup(inline_keyboard=kb)}

    async def handle(self) -> Any:
        m, call = utils.split_event(self.event)
        if not call:
            user_date = self.data["user_config"].current_time
            self.data["callback_data"] = MoodMonthCallback(
                user_id=self.event.from_user.id,
                year=user_date.year,
                month=user_date.month,
            )

        panel = await self.panel(self.data)

        if call:
            cd = self.cd
            assert isinstance(cd, MoodMonthCallback)
            await call.message.edit_text(**panel)  # type: ignore
            if cd.alert_marker and cd.marker != -1:
                mood = Mood.convert(cd.marker)
                await self.event.answer(
                    self.data["i18n"].mood_marker_selected(
                        marker=f"{str(mood)} {self.data['i18n'].get(f'mood.{mood.name.lower()}')}"
                    )
                )
        else:
            await m.reply(**panel)


class InputNoteContext(BaseModel):
    callback_data: MoodDayNote
    event: CallbackQuery


class MoodCommandArgs(utils.Regexp):
    __pattern__ = (
        r"(?P<day>\d{1,2})"
        r"|(?P<day_month>\d{1,2}\.\d{1,2})"
        r"|(?P<dmy>\d{1,2}\.\d{1,2}.\d{2,4})"
        r"|(?P<year>\d{4})"
        r"|(?P<yesterday>[вчера]{1,5})"
        r"|(?P<ereyesterday>[позавчера]{3,9})"
        r"|(?P<today>[сегодня]{1,7})"
        r"|(?P<tomorrow>[завтра]{1,6})"
        r"|(?P<overmorrow>[послезавтра]{3,11})"
    )

    day: int | None
    day_month: str | None
    dmy: str | None
    year: int | None
    ereyesterday: bool
    yesterday: bool
    today: bool
    tomorrow: bool
    overmorrow: bool

    @field_validator(
        "ereyesterday", "yesterday", "today", "tomorrow", "overmorrow", mode="before"
    )
    @classmethod
    def _validate_relative_days(cls, value: str | None):
        return bool(value)

    def generate_callback_data(self, user_config: UserConfig) -> OpenMoodDay:
        date = user_config.current_time
        if self.ereyesterday:
            date -= relativedelta(days=2)
        elif self.yesterday:
            date -= relativedelta(days=1)
        elif self.today:
            date = date
        elif self.tomorrow:
            date += relativedelta(days=1)
        elif self.overmorrow:
            date += relativedelta(days=2)
        elif self.day:
            date = date.replace(day=self.day)
        elif self.day_month:
            day, month = map(int, self.day_month.split("."))
            date = date.replace(day=day, month=month)
        elif self.dmy:
            day, month, year = self.dmy.split(".")
            if len(year) == 2:
                year = str(date.year)[:-2] + year
            date = date.replace(int(year), int(month), int(day))
        elif self.year:
            date = date.replace(year=self.year)
        return OpenMoodDay(user_id=user_config.user_id, **date_to_dict(date))


class MoodDayHandler(Handler[Message | CallbackQuery]):
    @classmethod
    def register(cls) -> None:
        flags.UNIQE_STATE(cls)

        mood_router.callback_query.register(
            cls,
            StateFilter(None, input_state.EDIT_NOTE, input_state.EXTEND_NOTE),
            OpenMoodDay.filter(),
        )
        mood_router.message.register(
            cls,
            StateFilter(None, input_state.EDIT_NOTE, input_state.EXTEND_NOTE),
            or_f(
                Command("mood"),
                MagicData(
                    (F.event.text | F.event.caption)
                    .regexp(
                        r"муд(?: *(?P<args>.+)|)", flags=re.IGNORECASE, mode="fullmatch"
                    )
                    .as_("command_match")
                ),
            ),
            MagicData(
                (
                    F.command.args.lower()
                    .func(MoodCommandArgs.fullmatch, user_config=F.user_config)
                    .as_("args")
                )
                | (
                    F.command_match.group("args")
                    .lower()
                    .func(MoodCommandArgs.fullmatch, user_config=F.user_config)
                    .as_("args")
                )
                | (F.command & ~F.command.args)
                | (F.command_match & ~F.command_match.group("args"))
            ),
        )

        mood_router.callback_query.register(
            cls.delete_note_handler,
            MoodDayNote.filter(F.action.in_({"delete-warning", "delete"})),
        )

        mood_router.callback_query.register(
            cls.edit_note_callback_handler,
            MoodDayNote.filter(F.action.in_({"edit", "extend"})),
        )

        mood_router.message.register(
            cls.edit_note_handler,
            F.html_text,
            or_f(
                StateFilter(input_state.EDIT_NOTE, input_state.EXTEND_NOTE),
                F.cast(
                    MoodNotifyConfigurator.is_replied_to_notify_job_panel_filter
                ).as_("notify_callback_data"),
            ),
            flags=dict(UNIQE_STATE=True),
        )

    @classmethod
    async def clear_state(cls, state: FSMContext):
        await state.set_state(None)
        await state.update_data(edit_note=None)

    async def handle(self):
        await self.clear_state(self.data["state"])
        m, call = utils.split_event(self.event)

        if call:
            panel = await self.panel(self.data)
            await m.edit_text(**panel)
        else:
            args = cast(MoodCommandArgs | None, self.data.get("args"))
            user_config = self.data["user_config"]
            if args:
                try:
                    callback_data = args.generate_callback_data(user_config)
                except Exception:
                    return
            else:
                user_time = user_config.current_time
                callback_data = OpenMoodDay(
                    user_id=user_config.user_id, **date_to_dict(user_time)
                )
            panel = await self.panel({**self.data, "callback_data": callback_data})
            method = m.answer if m.chat.type == "private" else m.reply
            await method(**panel)

    @classmethod
    async def edit_note_handler(
        cls,
        m: Message,
        notify_callback_data: MarkMoodDay | None = None,
        **data: Unpack[MiddlewareData],
    ):
        i18n = data["i18n"]
        edit_note_data = await data["state"].get_value("edit_note")
        assert edit_note_data or notify_callback_data

        if edit_note_data:
            edit_note_data = InputNoteContext.model_validate(
                edit_note_data, context={"bot": m.bot}
            )
            any_cd = edit_note_data.callback_data
        else:
            assert notify_callback_data is not None
            any_cd = notify_callback_data

        mood_month = await data["db"].get_mood_month(
            any_cd.user_id, year=any_cd.year, month=any_cd.month
        )
        note = mood_month.get_note(any_cd.day)

        is_replace_note = not note or (
            edit_note_data and edit_note_data.callback_data.action == "edit"
        )
        if is_replace_note:
            new_note = m.html_text
        else:
            new_note = cast(str, note) + "\n\n" + m.html_text
            new_note = new_note.strip()

        if len(new_note) > mood_month.DAY_NOTE_LIMIT_LENGHT:
            await m.reply(
                text=i18n.mood_day.note_too_long(
                    lenght=len(new_note), limit=mood_month.DAY_NOTE_LIMIT_LENGHT
                ),
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text=i18n.close(),
                                callback_data=DeleteMessage.merge(any_cd).pack(),
                            )
                        ]
                    ]
                ),
            )
            return

        await cls.clear_state(data["state"])
        mood_month.save_note(any_cd.day, new_note)
        await mood_month.merge()
        panel = await cls.panel({**data, "callback_data": OpenMoodDay.merge(any_cd)})
        await m.reply(**panel)

        if edit_note_data:
            await utils.suppress_error(
                edit_note_data.event.answer(i18n.mood_day.note_saved())
            )
            await utils.suppress_error(edit_note_data.event.message.delete())  # type: ignore
        else:
            await utils.suppress_error(m.reply_to_message.delete())

    @classmethod
    async def edit_note_callback_handler(
        cls, call: CallbackQuery, **data: Unpack[MiddlewareData]
    ):
        cd = data["callback_data"]
        assert isinstance(cd, MoodDayNote)

        panel = await cls.edit_note_panel(data)
        await call.message.edit_text(  # type: ignore
            **panel
        )
        input_data = InputNoteContext(event=call, callback_data=cd)
        await data["state"].update_data(
            edit_note=input_data.model_dump(exclude_none=True)
        )
        await data["state"].set_state(
            input_state.EDIT_NOTE if cd.action == "edit" else input_state.EXTEND_NOTE
        )

    @classmethod
    async def edit_note_panel(cls, data: MiddlewareData) -> dict[str, Any]:
        cd = data["callback_data"]
        assert isinstance(cd, MoodDayNote) and cd.action in ("edit", "extend")
        i18n = data["i18n"]
        text = i18n.mood_day.edit_note_panel(
            dmy=cd.date.strftime(r"%d.%m.%Y"),
            weekday=i18n.get(f"weekday_{cd.date.weekday() + 1}"),
            action=cd.action,
        )
        kb = [
            [
                InlineKeyboardButton(
                    text=i18n.cancel(), callback_data=OpenMoodDay.merge(cd).pack()
                )
            ],
        ]
        return dict(text=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

    @classmethod
    async def delete_note_warning_panel(cls, data: MiddlewareData) -> dict[str, Any]:
        cd = data["callback_data"]
        assert isinstance(cd, MoodDayNote)
        i18n = data["i18n"]
        text = i18n.mood_day.delete_note_warning(
            dmy=cd.date.strftime(r"%d.%m.%Y"),
            weekday=i18n.get(f"weekday_{cd.date.weekday() + 1}"),
        )
        kb = [
            [
                InlineKeyboardButton(
                    text=i18n.mood_day.delete_note(),
                    callback_data=cd.update(action="delete").pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text=i18n.cancel(), callback_data=OpenMoodDay.merge(cd).pack()
                )
            ],
        ]
        return dict(text=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

    @classmethod
    async def delete_note_handler(
        cls, call: CallbackQuery, **data: Unpack[MiddlewareData]
    ):
        cd = data["callback_data"]
        assert isinstance(cd, MoodDayNote)

        if cd.action == "delete-warning":
            panel = await cls.delete_note_warning_panel(data)
            await call.message.edit_text(  # type: ignore
                **panel
            )
            return

        assert cd.action == "delete"

        mood_month = await data["db"].get_mood_month(
            cd.user_id, year=cd.year, month=cd.month
        )
        mood_month.days_notes[cd.day - 1] = None
        await mood_month.merge()
        panel = await cls.panel({**data, "callback_data": OpenMoodDay.merge(cd)})
        await call.message.edit_text(  # type: ignore
            **panel
        )
        await utils.suppress_error(call.answer(data["i18n"].mood_day.note_deleted()))

    @classmethod
    async def panel(cls, data: MiddlewareData):
        MODE: Literal[1, 2] = 2

        cd = data["callback_data"]
        assert isinstance(cd, OpenMoodDay)
        mood_month = await data["db"].get_mood_month(
            cd.user_id, year=cd.year, month=cd.month
        )
        prev_day = cd.date - relativedelta(days=1)
        next_day = cd.date + relativedelta(days=1)
        day_mood = mood_month.get_mood(cd.date.day)
        day_note = dispay_day_note = mood_month.get_note(cd.day)
        # TODO hide notes in public chats
        i18n = data["i18n"]
        text = i18n.mood_day.main_panel(
            year=str(cd.date.year),
            month=i18n.get(f"month_{cd.date.month}"),
            day=str(cd.date.day),
            mood=day_mood.name.lower(),
            mood_emoji=str(day_mood),
            note=dispay_day_note or "none",
        )
        kb = [
            *(
                [
                    *utils.chunks(
                        [
                            InlineKeyboardButton(
                                text=f"{str(mood)} {data['i18n'].get(f'mood-{mood.name.lower()}')}",
                                callback_data=MarkMoodDay.merge(
                                    cd, value=int(mood), go_to="day"
                                ).pack(),
                            )
                            for mood in list(Mood)[1:]
                        ],
                        2,
                    ),
                    [
                        InlineKeyboardButton(
                            text=i18n.mood.unset(),
                            callback_data=MarkMoodDay.merge(
                                cd, value=int(Mood.UNSET), go_to="day"
                            ).pack(),
                        )
                    ],
                ]
                if MODE == 1
                else [
                    *utils.chunks(
                        [
                            InlineKeyboardButton(
                                text=(
                                    str(mood) or i18n.get(f"mood-{mood.name.lower()}")
                                ),
                                callback_data=MarkMoodDay.merge(
                                    cd, value=int(mood), go_to="day"
                                ).pack(),
                            )
                            for mood in (*list(Mood)[1:],)  # Mood.UNSET)
                        ],
                        6,
                    )
                ]
            ),
            *(
                [
                    [
                        InlineKeyboardButton(
                            text=i18n.mood_day.edit_note(),
                            callback_data=MoodDayNote.merge(cd, action="edit").pack(),
                        ),
                        InlineKeyboardButton(
                            # text=i18n.mood_day.delete_note(),
                            text="🗑",
                            callback_data=MoodDayNote.merge(
                                cd, action="delete-warning"
                            ).pack(),
                        ),
                        InlineKeyboardButton(
                            text=i18n.mood_day.extend_note(),
                            callback_data=MoodDayNote.merge(cd, action="extend").pack(),
                        ),
                    ],
                ]
                if day_note
                else [
                    [
                        InlineKeyboardButton(
                            text=i18n.mood_day.add_note(),
                            callback_data=MoodDayNote.merge(cd, action="edit").pack(),
                        )
                    ]
                ]
            ),
            [
                InlineKeyboardButton(
                    text="«",
                    callback_data=OpenMoodDay.merge(
                        cd, **date_to_dict(prev_day)
                    ).pack(),
                ),
                InlineKeyboardButton(
                    text=i18n.back(), callback_data=MoodMonthCallback.merge(cd).pack()
                ),
                InlineKeyboardButton(
                    text="»",
                    callback_data=OpenMoodDay.merge(
                        cd, **date_to_dict(next_day)
                    ).pack(),
                ),
            ],
        ]

        return {"text": text, "reply_markup": InlineKeyboardMarkup(inline_keyboard=kb)}


class MarkMoodDayHandler(Handler[CallbackQuery]):
    @classmethod
    def register(cls) -> None:
        mood_router.callback_query.register(MarkMoodDayHandler, MarkMoodDay.filter())

    async def handle(self):
        cd: MarkMoodDay = self.cd
        assert isinstance(cd, MarkMoodDay)
        mood_month = await self.data["db"].get_mood_month(
            cd.user_id, year=cd.year, month=cd.month
        )

        current_value = mood_month.get_mood(cd.day)
        new_value = Mood.convert(cd.value)
        if current_value == new_value:
            new_value = Mood.UNSET
        mood_month.save_mood(cd.day, new_value)
        await mood_month.merge()

        if cd.go_to == "day" or cd.go_to == "from_notify":
            self.data["callback_data"] = OpenMoodDay.merge(cd)
            panel = await MoodDayHandler.panel(self.data)
        else:
            self.data["callback_data"] = MoodMonthCallback.merge(cd)
            panel = await MoodMonthHandler.panel(self.data)

        await self.event.message.edit_text(**panel)  # type: ignore


class NotifyJobData(TypedDict):
    user_id: int
    date: datetime.date
    is_current_day: bool


# @flags.UNIQE_STATE
class MoodNotifyConfigurator(Handler[Message | CallbackQuery]):
    router = mood_router.include_router(Router())
    locks = defaultdict[str, asyncio.Lock](asyncio.Lock)

    @classmethod
    def register(cls):
        cls.router.message.middleware(cls.middleware)  # type: ignore
        cls.router.callback_query.middleware(cls.middleware)  # type: ignore

        cls.router.message.register(
            cls, default_state, Command("notify", magic=~F.args)
        )

        cls.router.callback_query.register(
            cls.handle_set_mood_state, MoodNotifySwitchState.filter()
        )

        cls.router.callback_query.register(
            cls.handle_set_mood_chat_id, MoodNotifySetChat.filter()
        )
        # cls.router.message.register(cls.handle_set_mood_chat_id, state tam i td)

        cls.router.callback_query.register(
            cls.handle_set_mood_time, MoodNotifySetTime.filter()
        )

        cls.router.callback_query.register(
            cls.open_choice_mood_time_panel, MoodNotifyChoiceTime.filter()
        )

        cls.router.callback_query.register(
            cls.handle_switch_day_type, MoodNotifySwitchDayType.filter()
        )

    @classmethod
    async def middleware(cls, handler, event, data: MiddlewareData):
        user_id = data["event_context"].user.id
        data["mood_cfg"] = await data["db"].get_mood_config(user_id)
        return await handler(event, data)

    @classmethod
    async def get_panel(
        cls,
        state: FSMContext,
        event: Message | CallbackQuery,
    ):
        if panel_msg := await state.get_value("panel_msg"):
            return Message.model_validate(panel_msg).as_(event.bot)

    @classmethod
    async def set_panel(
        cls,
        state: FSMContext,
        event: Message,
    ):
        await state.update_data(panel_msg=event.model_dump(exclude_none=True))

    @classmethod
    async def clear_state(cls, state: FSMContext):
        await state.set_state(None)
        await state.update_data(panel_msg=None)

    @classmethod
    async def answer(cls, event: Message | CallbackQuery, data: MiddlewareData, **kw):
        if panel_msg := await cls.get_panel(data["state"], event):
            try:
                await panel_msg.edit_text(**kw)
                return
            except Exception:
                logger.exception("")

        m, call = utils.split_event(event)
        if call:
            msg = await m.edit_text(**kw)
            await cls.set_panel(data["state"], m)
        else:
            method = m.answer if m.chat.type == "private" else m.reply
            msg = await method(**kw)
            await cls.set_panel(data["state"], msg)

    @classmethod
    async def answer_and_clear(
        cls, event: Message | CallbackQuery, data: MiddlewareData, **kw
    ):
        await cls.clear_state(data["state"])
        await cls.answer(event, data, **kw)

    @classmethod
    async def validate_chat(cls, event: TelegramObject, cfg: MoodConfig):
        if not cfg.notify_chat_id:
            return None
        try:
            return await event.bot.get_chat(cfg.notify_chat_id)
        except TelegramAPIError:
            logger.exception(f"{cfg.notify_chat_id=}")
            cfg.notify_chat_id = None
            cfg.notify_chat_topic_id
            await cfg.merge()
            return None

    @classmethod
    async def main_panel(
        cls, event: Message | CallbackQuery, data: MiddlewareData
    ) -> dict[str, Any]:
        cfg = data["mood_cfg"]
        m, call = utils.split_event(event)
        chat = await cls.validate_chat(event, cfg)
        chat_name = utils.chat_text_url(chat) if chat else "pm"
        cd_ctx = OwnedCallbackData(user_id=data["user_config"].user_id)
        i18n = data["i18n"]
        utc_offset = utils.utc_offset(data["user_config"].current_time)
        day_type = "current" if cfg.notify_current_day else "previos"
        invert_day_type = "current" if not cfg.notify_current_day else "previos"

        if cfg.notify_state:
            text = data["i18n"].mood_notify.enabled(
                chat=chat_name,
                time=f"{cfg.notify_time_str} <code>({utc_offset})</code>",
                day=day_type,
            )
            kb = [
                [
                    InlineKeyboardButton(
                        text=i18n.turn_off(),
                        callback_data=MoodNotifySwitchState.merge(cd_ctx).pack(),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=i18n.send_here(),
                        callback_data=MoodNotifySetChat.merge(
                            cd_ctx, chat_id=m.chat.id
                        ).pack(),
                    )
                    if not chat
                    else InlineKeyboardButton(
                        text=i18n.send_pm(),
                        callback_data=MoodNotifySetChat.merge(
                            cd_ctx, chat_id=None
                        ).pack(),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=i18n.get(f"mood_notify-notify_{invert_day_type}_day"),
                        callback_data=MoodNotifySwitchDayType.merge(cd_ctx).pack(),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=f"{cfg.notify_time_emoji} {cfg.notify_time_str} ({i18n.change()})",
                        callback_data=MoodNotifyChoiceTime.merge(cd_ctx).pack(),
                    )
                ],
            ]
        else:
            text = i18n.mood_notify.disabled()
            kb = [
                [
                    InlineKeyboardButton(
                        text=i18n.turn_on(),
                        callback_data=MoodNotifySwitchState.merge(cd_ctx).pack(),
                    )
                ],
            ]

        if main.DEV_MODE:
            text += (
                "\n\n-----\n\n"
                + f"<code>{utils.escape_html(cfg.model_dump_json(indent=4))}</code>"
            )
        return dict(text=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

    @classmethod
    async def panel_choice_time(cls, data: MiddlewareData) -> dict[str, Any]:
        user_id = data["user_config"].user_id
        text = data["i18n"].mood_notify.select_time()
        kb = utils.chunks(
            (
                InlineKeyboardButton(
                    text=f"{hour_time:%H:%M}",
                    callback_data=MoodNotifySetTime(
                        user_id=user_id, time=f"{hour_time:%H:%M}"
                    ).pack(),
                )
                for hour_time in map(datetime.time, range(24))
            ),
            5,
        )
        return dict(text=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

    async def handle(self):
        panel = await self.main_panel(self.event, self.data)
        await self.answer_and_clear(self.event, self.data, **panel)

    @classmethod
    async def handle_set_mood_state(
        cls, call: CallbackQuery, **data: Unpack[MiddlewareData]
    ):
        cfg = data["mood_cfg"]
        cfg.notify_state = not cfg.notify_state
        await cfg.merge()
        panel = await cls.main_panel(call, data)
        await cls.answer(call, data, **panel)

    @classmethod
    async def handle_switch_day_type(
        cls, call: CallbackQuery, **data: Unpack[MiddlewareData]
    ):
        cfg = data["mood_cfg"]
        cfg.notify_current_day = not cfg.notify_current_day
        await cfg.merge()
        panel = await cls.main_panel(call, data)
        await cls.answer(call, data, **panel)

    @classmethod
    async def handle_set_mood_chat_id(
        cls,
        event: Message | CallbackQuery,
        chat_id: int | None = None,
        **data: Unpack[MiddlewareData],
    ):
        # await data["state"].set_state(None)

        m, call = utils.split_event(event)

        if chat_id is None:
            chat_id = cast(MoodNotifySetChat, data["callback_data"]).chat_id

        cfg = data["mood_cfg"]
        cfg.notify_chat_id = chat_id
        cfg.notify_chat_topic_id = utils.get_topic_id(m)
        await cfg.merge()
        panel = await cls.main_panel(m, data)
        await cls.answer(event, data, **panel)
        # await m.delete()

    @classmethod
    async def handle_set_mood_time(
        cls, event: Message | CallbackQuery, **data: Unpack[MiddlewareData]
    ):
        await data["state"].set_state(None)
        cfg = data["mood_cfg"]
        m, call = utils.split_event(event)
        if call:
            callback_data: MoodNotifySetTime = data["callback_data"]
            notify_time = callback_data.time
        else:
            notify_time = cast(str, m.text)

        cfg.notify_time = notify_time  # type: ignore
        await cfg.merge()
        panel = await cls.main_panel(event, data)
        await cls.answer(event, data, **panel)

    @classmethod
    async def open_choice_mood_time_panel(
        cls, call: CallbackQuery, **data: Unpack[MiddlewareData]
    ):
        await call.message.edit_text(  # type: ignore
            **await cls.panel_choice_time(data)
        )

    @classmethod
    @asynccontextmanager
    async def notify_job_lock(cls, chat_id: int | str):
        chat_lock_key = f"chat_lock:{chat_id}"

        async with cls.locks[chat_lock_key]:
            yield

        await asyncio.sleep(3)

    @classmethod
    async def on_change_config(cls, mood_cfg: MoodConfig):
        scheduler = dp["scheduler"]
        user_config = await dp["db"].get_user(mood_cfg.user_id)
        job_id = f"mood_notify:{mood_cfg.user_id}"
        date = datetime.datetime.now(user_config.tz).date()
        if not mood_cfg.notify_current_day:
            date -= relativedelta(days=1)

        with suppress(JobLookupError):
            scheduler.remove_job(job_id)

        if not mood_cfg.notify_state:
            return

        scheduler.add_job(
            notify_job_callback_proxy,
            kwargs=NotifyJobData(
                user_id=mood_cfg.user_id,
                date=date,
                is_current_day=mood_cfg.notify_current_day,
            ),
            id=job_id,
            trigger="cron",
            hour=mood_cfg.notify_time.hour,
            minute=mood_cfg.notify_time.minute,
            second=mood_cfg.notify_time.second,
            timezone=user_config.tz,
            misfire_grace_time=86400 * 7,
        )

    @classmethod
    def is_replied_to_notify_job_panel_filter(cls, m: Message):
        if not m.reply_to_message:
            return
        try:
            match m.reply_to_message.reply_markup:
                case InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(callback_data=CD1),
                            InlineKeyboardButton(callback_data=CD2),
                        ],
                        [
                            InlineKeyboardButton(callback_data=CD3),
                            InlineKeyboardButton(callback_data=CD4),
                        ],
                        [
                            InlineKeyboardButton(callback_data=CD5),
                            InlineKeyboardButton(callback_data=CD6),
                        ],
                        [
                            InlineKeyboardButton(callback_data=CD7),
                        ],
                    ]
                ) if all(
                    MarkMoodDay.unpack(cd)  # type: ignore
                    for cd in (CD1, CD2, CD3, CD4, CD5, CD6)  # type: ignore
                ) and DeleteMessage.unpack(CD7):  # type: ignore
                    cd = MarkMoodDay.unpack(CD1)  # type: ignore
                    if m.from_user.id == cd.user_id:
                        return cd
        except ValueError | TypeError:
            pass

    @classmethod
    async def notify_job_panel(
        cls, mood_cfg: MoodConfig, date: datetime.date, is_current_day: bool
    ) -> dict[str, Any]:
        user_config = await dp["db"].get_user(mood_cfg.user_id)
        i18n = cast(
            I18nContext, dp["i18n_middleware"].new_context(user_config.lang_code, {})
        )
        user_name = user_config.text_url
        user_name += f'<a href="tg://user?id={user_config.user_id}">\xad</a>'
        text = i18n.mood_notify.notification(
            user_name=user_config.text_url,
            dmy=date.strftime(r"%d.%m.%Y"),
            weekday=i18n.get(f"weekday_{date.weekday() + 1}"),
            day="current" if mood_cfg.notify_current_day else "previos",
        )
        kb = [
            *utils.chunks(
                (
                    InlineKeyboardButton(
                        text=f"{str(mood)} {i18n.get(f'mood-{mood.name.lower()}')}",
                        callback_data=MarkMoodDay(
                            user_id=user_config.user_id,
                            value=int(mood),
                            year=date.year,
                            month=date.month,
                            day=date.day,
                            go_to="from_notify",
                        ).pack(),
                    )
                    for mood in (*list(Mood)[1:],)
                ),
                2,
            ),
            [
                InlineKeyboardButton(
                    text=i18n.close(),
                    callback_data=DeleteMessage(user_id=user_config.user_id).pack(),
                )
            ],
        ]
        return dict(text=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

    @classmethod
    async def notify_job_callback(
        cls, user_id: int, date: datetime.date, is_current_day: bool
    ):
        bot = dp["main_bot"]
        mood_config = await dp["db"].get_mood_config(user_id)
        job_id = f"mood_notify:{mood_config.user_id}"

        dp["scheduler"].modify_job(
            job_id=job_id,
            kwargs=NotifyJobData(
                user_id=user_id,
                date=date + relativedelta(days=1),
                is_current_day=is_current_day,
            ),
        )

        panel = await cls.notify_job_panel(mood_config, date, is_current_day)
        request = SendMessage(
            chat_id=mood_config.notify_chat_id or user_id,
            message_thread_id=mood_config.notify_chat_topic_id,
            disable_notification=False,
            **panel,
        ).as_(bot)
        if mood_config.notify_chat_id:
            if last_message := await dp["db"].get_last_message(
                mood_config.notify_chat_id,
                topic_id=mood_config.notify_chat_topic_id,
                user_id=user_id,
            ):
                request.reply_parameters = ReplyParameters(
                    message_id=last_message.message.message_id
                )

        try:
            try:
                async with cls.notify_job_lock(request.chat_id):
                    await request
            except TelegramAPIError:
                if (
                    mood_config.notify_chat_id is None
                    or mood_config.notify_chat_id == mood_config.user_id
                ):
                    raise

                # try send to PM
                request.chat_id = mood_config.user_id
                request.message_thread_id = None
                try:
                    async with cls.notify_job_lock(request.chat_id):
                        await request
                except TelegramAPIError:
                    raise
                else:
                    mood_config.notify_chat_id = None
                    mood_config.notify_chat_topic_id = None
                    await mood_config.merge()
        except TelegramAPIError:
            logger.exception(f"cant send message to {mood_config.user_id}")
            mood_config.notify_state = False
            await mood_config.merge()


async def notify_job_callback_proxy(**data: Unpack[NotifyJobData]):
    # apscheduler only support module-side funcs
    data.setdefault("is_current_day", False)
    return await MoodNotifyConfigurator.notify_job_callback(**data)
