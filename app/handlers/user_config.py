from __future__ import annotations

from typing import Any


from aiogram.types import (
    Message,
    CallbackQuery,
)


from app import utils

from app.handlers.common import Handler
from app.handlers.middlewares import MiddlewareData


class UserConfigurator(Handler[Message | CallbackQuery]):
    @classmethod
    def register(cls) -> None: ...

    @classmethod
    async def main_panel(cls, data: MiddlewareData) -> dict[str, Any]: ...

    async def handle(self):
        m, call = utils.split_event(self.event)
        panel = await self.main_panel(self.data)
        if call:
            await m.edit_text(**panel)
        elif m.chat.type == "private":
            await m.answer(**panel)
        else:
            await m.reply(**panel)
