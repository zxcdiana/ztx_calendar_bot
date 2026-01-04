import html
import inspect
import logging
from typing import Awaitable, Iterable
from aiogram.types import Message, CallbackQuery


__all__ = (
    "get_logger",
    "suppress_error",
    "chunks",
    "escape_html",
    "split_event",
)


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


def split_event(
    event: Message | CallbackQuery,
) -> tuple[Message, CallbackQuery | None]:
    if isinstance(event, CallbackQuery):
        return event.message, event  # pyright: ignore[reportReturnType]
    else:
        return event, None
