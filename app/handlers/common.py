from __future__ import annotations

from typing import ClassVar
from abc import abstractmethod


from aiogram import flags
from aiogram.types import Message, CallbackQuery
from aiogram.handlers import BaseHandler as BaseHandler

from app.main import main_router

from app.handlers.middlewares import MiddlewareData
from app.handlers.callback_data import DeleteMessage, empty_callback_data


@flags.UNIQE_STATE
@main_router.callback_query(DeleteMessage.filter())
async def delete_message(call: CallbackQuery):
    m = call.message
    if not isinstance(m, Message):
        await call.answer(f"unknown: {type(call.message).__name__}")
        return

    try:
        if m.text:
            await m.edit_text(inline_message_id=call.inline_message_id, text="\xad")
        elif m.caption:
            await m.edit_caption(
                inline_message_id=call.inline_message_id, caption="\xad"
            )
    finally:
        await m.delete()


@flags.UNIQE_STATE
@main_router.callback_query(empty_callback_data.filter())
async def handle_empty_button(call: CallbackQuery):
    await call.answer(cache_time=99999)


class Handler[T](BaseHandler[T]):
    data: MiddlewareData  # type: ignore

    __all_handlers__: ClassVar[list[Handler]] = []
    __is_registered__: ClassVar[bool] = False

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        Handler.__all_handlers__.append(cls)  # type: ignore

    @classmethod
    def register_all(cls):
        if cls.__is_registered__:
            raise RuntimeError("handlers already registered")

        cls.__is_registered__ = True
        for handler in cls.__all_handlers__:
            handler.register()

    @classmethod
    @abstractmethod
    def register(cls) -> None:
        raise NotImplementedError

    @property
    def cd(self):
        return self.data["callback_data"]
