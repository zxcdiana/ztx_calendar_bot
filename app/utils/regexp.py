import re
import sys
from typing import (
    Any,
    Callable,
    ClassVar,
    Generator,
    Self,
    Unpack,
    cast,
)

from pydantic import BaseModel, ConfigDict, PrivateAttr


class Regexp(BaseModel):
    __pattern__: ClassVar[str | re.Pattern[str]]
    __reflags__: ClassVar[re.RegexFlag | int] = 0
    _match: re.Match[str] = PrivateAttr()

    model_config = ConfigDict(
        extra="allow", validate_assignment=True, arbitrary_types_allowed=True
    )

    def model_post_init(self, context: Any) -> None:
        if isinstance(context, dict) and "match" in context:
            self._match = context["match"]

    def __init_subclass__(cls, **kwargs: Unpack[ConfigDict]):
        super().__init_subclass__(**kwargs)

        if isinstance(cls.__pattern__, str):
            cls.__pattern__ = re.compile(cls.__pattern__, flags=cls.__reflags__)

        assert isinstance(cls.__pattern__, re.Pattern), f"{type(cls.__pattern__)=}"

    @classmethod
    def pattern(cls) -> re.Pattern[str]:
        return cast(re.Pattern[str], cls.__pattern__)

    @classmethod
    def from_match(cls, match: re.Match[str], **kw) -> Self:
        kw.update(match.groupdict())
        return cls.model_validate(kw, context={"match": match})

    @classmethod
    def match(
        cls, string: str, pos: int = 0, endpos: int = sys.maxsize, **kw
    ) -> Self | None:
        if match := cls.pattern().match(string=string, pos=pos, endpos=endpos):
            return cls.from_match(match, **kw)

    @classmethod
    def search(
        cls, string: str, pos: int = 0, endpos: int = sys.maxsize, **kw
    ) -> Self | None:
        if match := cls.pattern().search(string=string, pos=pos, endpos=endpos):
            return cls.from_match(match, **kw)

    @classmethod
    def fullmatch(
        cls, string: str, pos: int = 0, endpos: int = sys.maxsize, **kw
    ) -> Self | None:
        if match := cls.pattern().fullmatch(string=string, pos=pos, endpos=endpos):
            return cls.from_match(match, **kw)

    @classmethod
    def findall(cls, string: str, pos: int = 0, endpos: int = sys.maxsize) -> list[str]:
        return cls.pattern().findall(
            string=string,
            pos=pos,
            endpos=endpos,
        )

    @classmethod
    def finditer(
        cls, string: str, pos: int = 0, endpos: int = sys.maxsize, **kw
    ) -> Generator[Self]:
        for match in cls.pattern().finditer(
            string=string,
            pos=pos,
            endpos=endpos,
        ):
            yield cls.from_match(match, **kw)

    @classmethod
    def sub(
        cls,
        repl: str | Callable[[Self], str],  # pyright: ignore[reportRedeclaration]
        string: str,
        count: int = 0,
        **kw,
    ) -> str:
        if callable(repl):
            orig_repl = repl

            def repl(match: re.Match[str]):
                return orig_repl(cls.from_match(match, **kw))

        return cls.pattern().sub(repl=repl, string=string, count=count)
