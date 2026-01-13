from __future__ import annotations

from abc import ABCMeta
from typing import Awaitable, Iterable
import html
import inspect
import logging
import datetime

from aiogram.types import Message, CallbackQuery, Chat


__all__ = (
    "get_logger",
    "suppress_error",
    "chunks",
    "escape_html",
    "split_event",
)


class Singleton(ABCMeta):
    def __new__(mcls, name, bases, namespace, /, **kwargs):
        cls = super().__new__(mcls, name, bases, namespace, **kwargs)
        raw_init = cls.__init__
        is_initialized = False

        def __init_wrapper__(*a, **kw):
            nonlocal is_initialized
            if is_initialized:
                raise RuntimeError(f"{cls.__name__} already initialized")
            is_initialized = True
            return raw_init(*a, **kw)

        cls.__init__ = __init_wrapper__
        return cls


def get_logger(name: str | None = None) -> logging.Logger:
    if name is None:
        name = inspect.getmodule(inspect.currentframe().f_back).__name__

    return logging.getLogger(name)


logger = get_logger()


async def suppress_error[T](coro: Awaitable[T]) -> T | None:
    try:
        return await coro
    except Exception:
        logger.exception("")


def chunks[T](iterable: Iterable[T], n: int) -> list[list[T]]:
    iterable = list(iterable)
    return [iterable[i : i + n] for i in range(0, len(iterable), n)]


def escape_html(s: str) -> str:
    return html.escape(s, quote=False)


def utc_offset(date: datetime.datetime):
    delta = date.utcoffset()
    assert delta is not None
    hours, minutes = map(int, divmod(delta.total_seconds() / 60, 60))
    result = f"{'+' if hours >= 0 else ''}{hours}"
    if minutes:
        minutes = str(minutes)
        if len(minutes) == 1:
            minutes = f"0{minutes}"
        result += f":{minutes}"
    return result


def split_event(
    event: Message | CallbackQuery,
) -> tuple[Message, CallbackQuery | None]:
    if isinstance(event, CallbackQuery):
        return event.message, event  # pyright: ignore[reportReturnType]
    else:
        return event, None


def chat_url(chat: Chat):
    is_private = chat.type == "private"
    if chat.username:
        url = f"https://t.me/{chat.username}"
    elif is_private:
        url = f"tg://openmessage?user_id={chat.id}"
    else:
        chat_id = str(chat.id).removeprefix("-100")
        url = f"https://t.me/c/{chat_id}"

    return url


def chat_text_url(chat: Chat):
    return f'<a href="{chat_url(chat)}">{escape_html(chat.full_name)}</a>'


def time_emoji(time_obj: datetime.time | datetime.datetime):
    emojis = ["🕛"] + list("🕐🕑🕒🕓🕔🕕🕖🕗🕘🕙🕚🕛")
    return emojis[time_obj.hour if time_obj.hour < 12 else time_obj.hour - 12]
