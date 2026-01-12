from aiogram import F, Router, flags
from aiogram.types import Message, InlineKeyboardMarkup
from aiogram.filters import Command

from app.main import commands_router

from app.handlers.common import Handler
from app.handlers.middlewares import MiddlewareData


class StartCommand(Handler[Message]):
    router = commands_router.include_router(Router())

    @classmethod
    def register(cls) -> None:
        cls.router.message.middleware(cls.middleware)  # type: ignore
        flags.UNIQE_STATE(cls)
        cls.router.message.register(StartCommand, Command("start", magic=~F.args))

    @classmethod
    async def middleware(cls, handler, event, data: MiddlewareData):
        await cls.purge_state(data)
        return await handler(event, data)

    @classmethod
    async def purge_state(cls, data: MiddlewareData):
        from app.handlers.mood import MoodNotifyConfigurator, MoodDayHandler

        state = data["state"]
        await MoodDayHandler.clear_state(state)
        await MoodNotifyConfigurator.clear_state(state)
        await state.clear()

    async def handle(self):
        await self.purge_state(self.data)
        command = self.data["command"]
        if not command.args:
            return await self.handle_no_args()

    async def handle_no_args(self):
        text = self.data["i18n"].command.start(
            user_name=self.data["user_config"].text_url
        )
        kb = [[]]
        method = (
            self.event.answer if self.event.chat.type == "private" else self.event.reply
        )
        await method(text=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
