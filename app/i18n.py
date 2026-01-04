from __future__ import annotations

from typing import TYPE_CHECKING, cast

from aiogram.dispatcher.middlewares.user_context import EventContext

from aiogram_i18n import I18nMiddleware
from aiogram_i18n.managers import BaseManager
from aiogram_i18n.cores import FluentRuntimeCore


if not TYPE_CHECKING:
    from aiogram_i18n import I18nContext, L
    from aiogram_i18n.lazy import LazyFactory

else:
    from aiogram_i18n import I18nContext as _I18nContext
    from aiogram_i18n.lazy import LazyFactory as _LazyFactory

    from app._stub import I18nStub  # type: ignore

    class I18nContext(_I18nContext, I18nStub): ...

    class LazyFactory(_LazyFactory, I18nStub): ...

    L = LazyFactory()

    from app.database import UserConfig


__all__ = (
    "I18nContext",
    "LazyFactory",
    "I18nMiddlewareManager",
    "FluentRuntimeCore",
    "L",
)


class I18nMiddlewareManager(BaseManager):
    async def get_locale(
        self,
        i18n_middleware: I18nMiddleware,
        event_context: EventContext | None = None,
        user_config: UserConfig | None = None,
    ):
        if user_config is not None and user_config.locale is not None:
            locale = user_config.lang_code
        elif event_context is not None and event_context.user:
            locale = event_context.user.language_code
        else:
            locale = None

        return (
            locale
            if locale is not None and locale in i18n_middleware.core.locales
            else cast(str, i18n_middleware.core.default_locale)
        )

    async def set_locale(*_):
        pass
