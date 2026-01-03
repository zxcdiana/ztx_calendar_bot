import html
import inspect
import logging
import re
from typing import Awaitable, Iterable, TypeVar
from aiogram.types import Message, CallbackQuery


__all__ = (
    "get_logger",
    "suppress_error",
    "chunks",
    "escape_html",
    "split_event",
    "emoji",
    "remove_html_tags",
    "truncate_text",
    "split_text",
)


def get_logger(name: str | None = None) -> logging.Logger:
    if name is None:
        name = inspect.getmodule(inspect.currentframe().f_back).__name__

    return logging.getLogger(name)


logger = get_logger()
T = TypeVar("T")


async def suppress_error(coro: Awaitable[T]) -> T | None:
    try:
        return await coro
    except Exception:
        logger.exception("")


def chunks(iterable: Iterable[T], n: int) -> list[list[T]]:
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


def emoji(emoji: str, custom_emoji_id: int | None = None):
    """html emoji format"""
    if not custom_emoji_id:
        return emoji
    return f'<tg-emoji emoji-id="{custom_emoji_id}">{emoji}</tg-emoji>'


remove_html_pattern = re.compile(r"<.+?>|</.+?>", re.ASCII)


def remove_html_tags(text: str, unescape: bool = True):
    if unescape:
        text = html.unescape(text)
    text = remove_html_pattern.sub("", text)
    return text


def truncate_text(text: str, lenght: int, suffix: str = ".."):
    if len(text) <= lenght:
        return text
    truncated = text[: -(len(text) - len(suffix))] + suffix
    return truncated


def split_text(text: str, maxlen: int) -> list[str]:
    output: list[str] = []
    chunk: list[str] = []
    chunk_len = 0

    for line in text.splitlines():
        line_len = len(line)
        if chunk:
            line_len += len("\n")
        if chunk_len + line_len > maxlen:
            output.append("\n".join(chunk))
            chunk.clear()
            chunk_len = 0
        else:
            chunk.append(line)
            chunk_len += line_len

    if chunk:
        output.append("\n".join(chunk))
    if not output:
        return list(map(str().join, chunks(text, maxlen)))
    return output
