from typing import Any

from aiogram import F
from aiogram.filters import MagicData
from aiogram.filters.logic import _AndFilter
from aiogram.dispatcher.event.handler import CallbackType, FilterObject

from app.main import admin_router, commands_router, main_router

from app.handlers.middlewares import MiddlewareData


admin_f = MagicData(F.event_context.user_id.in_(F.app_cfg.owners))
admin_router.callback_query.filter(admin_f)
admin_router.inline_query.filter(admin_f)
admin_router.message.filter(admin_f)

commands_router.message.filter(~F.forward_origin & ~F.via_bot)


class ContextualAndFilter(_AndFilter):
    async def __call__(self, *args: Any, **kwargs: Any) -> bool | dict[str, Any]:
        final_result = {}

        for target in self.targets:
            result = await target.call(*args, **kwargs)
            if not result:
                return False
            if isinstance(result, dict):
                final_result.update(result)
                kwargs.update(result)  # obtain context for next filter

        if final_result:
            return final_result
        return True


def ctx_and_f(*targets: CallbackType) -> ContextualAndFilter:
    return ContextualAndFilter(*(FilterObject(target) for target in targets))


@main_router.message.middleware  # type: ignore
@main_router.callback_query.middleware  # type: ignore
async def state_filter(handler, event, data: MiddlewareData):
    """
    skip event if user has any state when handler not require state
    """
    raw_state = data.get("raw_state")
    event_handler = data.get("handler")

    if (
        raw_state is None
        or event_handler is not None
        and event_handler.flags.get("UNIQE_STATE")
    ):
        return await handler(event, data)
