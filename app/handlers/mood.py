import math
from typing import TYPE_CHECKING, Any
from datetime import datetime
from dateutil.relativedelta import relativedelta

from aiogram import F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.handlers import BaseHandler as _BaseHandler
from aiogram.filters import or_f, Command

from sqlalchemy import select


from app import utils
from app.handlers.callback_data import (
    MarkMoodDay,
    OpenMoodDay,
    MoodMonthCallback,
    empty_callback_data,
)
from app.handlers.middlewares import MiddlewareData
from app.i18n import I18nContext
from app.mood import (
    Mood,
    date_to_dict,
)
from app.database import MoodMonth, orm
from app.main import dp, mood_router


class BaseHandler[T](_BaseHandler[T]):
    data: MiddlewareData  # type: ignore
    callback_data: Any

    @property
    def cd(self):
        if TYPE_CHECKING:
            return self.callback_data
        else:
            return self.data["callback_data"]


class MoodMonthHandler(BaseHandler[Message | CallbackQuery]):
    @staticmethod
    def str_month(i18n: I18nContext, *, month: int):
        return i18n.get(f"month_{month}")

    @staticmethod
    async def get_mood_month(cd: MoodMonthCallback):
        async with dp["db"].sessionmaker() as session:
            stmt = (
                select(orm.MoodMonth)
                .where(orm.MoodMonth.user_id == cd.user_id)
                .where(orm.MoodMonth.year == cd.year)
                .where(orm.MoodMonth.month == cd.month)
            )
            if mood_month_orm := await session.scalar(stmt):
                return MoodMonth.model_validate(mood_month_orm)

            mood_month = MoodMonth(
                user_id=cd.user_id,
                year=cd.year,
                month=cd.month,
            )
            session.add(orm.MoodMonth.from_model(mood_month))
            await session.commit()

            return mood_month

    @classmethod
    async def panel(cls, data: MiddlewareData):
        cd = data["callback_data"]
        assert isinstance(cd, MoodMonthCallback)
        mood_month = await cls.get_mood_month(cd)
        mark = cd.marker
        text = data["i18n"].mood_month(
            year=str(cd.year), month=cls.str_month(data["i18n"], month=cd.month)
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
                    cd, month=workflow_date.month
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
                    cd, month=workflow_date.month
                ).pack(),
            )
        ]
        kb += [row]
        return {"text": text, "reply_markup": InlineKeyboardMarkup(inline_keyboard=kb)}

    async def handle(self) -> Any:
        m, call = utils.split_event(self.event)
        if not call:
            user_date = datetime.now(self.data["user_config"].tz)
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


mood_router.message.register(
    MoodMonthHandler, or_f(Command("mood", magic=~F.args), F.text.lower() == "муд")
)
mood_router.callback_query.register(MoodMonthHandler, MoodMonthCallback.filter())


class OpenMoodDayHandler(BaseHandler[CallbackQuery]):
    callback_data: OpenMoodDay

    @classmethod
    async def panel(cls, data: MiddlewareData):
        cd = data["callback_data"]
        assert isinstance(cd, OpenMoodDay)
        mood_month = await MoodMonthHandler.get_mood_month(cd)
        prev_day = cd.date - relativedelta(days=1)
        next_day = cd.date + relativedelta(days=1)
        mood = mood_month.get_mood(cd.date.day)
        text = data["i18n"].mood_day(
            year=str(cd.date.year),
            month=data["i18n"].get(f"month_{cd.date.month}"),
            day=str(cd.date.day),
            mood=mood.name.lower(),
            mood_emoji=str(mood),
        )
        kb = [
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
                    text=data["i18n"].mood.unset(),
                    callback_data=MarkMoodDay.merge(
                        cd, value=int(Mood.UNSET), go_to="day"
                    ).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="«",
                    callback_data=OpenMoodDay.merge(
                        cd, **date_to_dict(prev_day)
                    ).pack(),
                ),
                InlineKeyboardButton(
                    text="\xad", callback_data=MoodMonthCallback.merge(cd).pack()
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

    async def handle(self):
        panel = await self.panel(self.data)
        await self.event.message.edit_text(**panel)  # type: ignore


mood_router.callback_query.register(OpenMoodDayHandler, OpenMoodDay.filter())


class MarkMoodDayHandler(BaseHandler[CallbackQuery]):
    callback_data: MarkMoodDay

    async def handle(self):
        cd: MarkMoodDay = self.cd
        assert isinstance(cd, MarkMoodDay)
        mood_month = await MoodMonthHandler.get_mood_month(cd)
        mood_month.days[cd.day - 1] = Mood.convert(cd.value)

        async with self.data["db"].begin() as session:
            await session.merge(orm.MoodMonth.from_model(mood_month))

        if cd.go_to == "day":
            self.data["callback_data"] = OpenMoodDay.merge(cd)
            panel = await OpenMoodDayHandler.panel(self.data)
        else:
            self.data["callback_data"] = MoodMonthCallback.merge(cd)
            panel = await MoodMonthHandler.panel(self.data)

        await self.event.message.edit_text(**panel)  # type: ignore


mood_router.callback_query.register(MarkMoodDayHandler, MarkMoodDay.filter())
