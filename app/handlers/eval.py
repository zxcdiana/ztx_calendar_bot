# ruff: noqa: E401, F401

import re
import sys
import meval
import inspect
import traceback
from contextlib import suppress
from dataclasses import dataclass
from unittest.mock import sentinel
from typing import Any, Self, Union

from aiogram.types import Message
from aiogram.filters import Command

from app.main import admin_router
from app import utils


__all__ = ("AsyncEval",)


UNSET = sentinel._UNSET_EVAL_RESULT


@dataclass()
class AsyncEval:
    code: str
    result: Union[UNSET, Any]
    exception: Exception | None

    @classmethod
    async def run(cls, code: str, vars: dict[str, Any] = {}) -> Self:
        result = UNSET
        exception = None

        vars.pop("code", None)
        vars.pop("globs", None)
        try:
            result = await meval.meval(
                code, inspect.currentframe().f_back.f_globals, **vars
            )
        except Exception as e:
            exception = e
        return cls(code=code, result=result, exception=exception)

    async def format(self, html: bool = False, stack_offset: int = 2) -> str:
        return await self.format_result(html) or await self.format_exception(
            html, stack_offset=stack_offset
        )

    async def format_exception(self, html: bool = False, stack_offset: int = 2) -> str:
        if self.exception is None:
            return ""
        try:
            raise self.exception
        except Exception:
            full_traceback = traceback.format_exc().replace(
                "Traceback (most recent call last):\n", "", 1
            )
            full_traceback = utils.escape_html(full_traceback)
            line_regex = re.compile(
                r'  File "(?P<file>.*?)", line (?P<line>[0-9]+), in (?P<name>.+)'
            )
            # path = str(APP_DIR.parent)
            # # ruff: noqa: E731

            # handle_file_path = lambda x: x[len(path) :] if x.startswith(path) else x
            handle_file_path = lambda x: x
            e = utils.escape_html

            if html:
                handle_line = lambda x: (  #
                    f"👉🏿 <code>{(handle_file_path(x.group('file')))}:{e(x.group('line'))}</code> <b>in</b> <code>{e(x.group('name'))}</code>"
                )
            else:
                handle_line = lambda x: (
                    f"👉🏿 {e(handle_file_path(x.group('file')))}:{e(x.group('line'))} in {e(x.group('name'))}"
                )

            lines = full_traceback.splitlines()
            for line in lines.copy():
                if r := line_regex.search(line):
                    if stack_offset == 0:
                        lines = lines[lines.index(line) :]
                    else:
                        stack_offset -= 1

            return "\n".join(
                handle_line(r) if (r := line_regex.search(x)) else x for x in lines
            )

    async def format_result(self, html: bool = False) -> str:
        if self.result is UNSET:
            return ""

        result = self.result

        with suppress(Exception):
            if hasattr(result, "stringify"):
                result = result.stringify()

        if html:
            return f"<code>{utils.escape_html(str(result))}</code>"

        return str(result)


@admin_router.message(Command("eval", "e"))
async def eval_command(m: Message, **data):
    code = data.get("command").args

    if code is None:
        await m.answer("???")
        return

    result = await AsyncEval.run(
        code,
        {**sys.modules, **data, "data": data, "m": m, "r": m.reply_to_message},
    )
    text = await result.format(html=True)
    await m.answer(f"<blockquote expandable>{text}</blockquote>")
