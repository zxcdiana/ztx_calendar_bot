from typing import TYPE_CHECKING, cast

from aiogram.dispatcher.middlewares.user_context import EventContext

from aiogram_i18n import I18nMiddleware
from aiogram_i18n.managers import BaseManager
from aiogram_i18n.cores import FluentRuntimeCore

from app.types import UserConfig

if not TYPE_CHECKING:
    from aiogram_i18n import I18nContext, L
    from aiogram_i18n.lazy import LazyFactory

else:
    from aiogram_i18n import I18nContext as _I18nContext
    from aiogram_i18n.lazy import LazyFactory as _LazyFactory

    from stub import I18nStub  # pyright: ignore[reportMissingModuleSource]

    class I18nContext(_I18nContext, I18nStub): ...

    class LazyFactory(_LazyFactory, I18nStub): ...

    L = LazyFactory()

from app.config import LOCALES_DIR


__all__ = (
    "I18nContext",
    "LazyFactory",
    "L",
)


class I18nMiddlewareManager(BaseManager):
    async def get_locale(
        self,
        i18n_middleware: I18nMiddleware,
        event_context: EventContext | None = None,
        user_config: UserConfig | None = None,
    ):
        locale = cast(str, i18n_middleware.core.default_locale)

        if user_config is not None and user_config.locale is not None:
            locale = user_config.lang_code

        elif event_context is not None and event_context.user:
            locale = event_context.user.language_code or locale

        return locale if locale in {"ru"} else locale

    async def set_locale(*_):
        pass


def create_i18n_middleware():
    return I18nMiddleware(
        core=FluentRuntimeCore(
            path=LOCALES_DIR,
        ),
        manager=I18nMiddlewareManager(),
        default_locale="ru",
    )
