from aiogram import F
from aiogram.types import CallbackQuery
from aiogram.filters import MagicData

from app.handlers.middlewares import MiddlewareData
from app.main import main_router, admin_router, commands_router


@main_router.callback_query.middleware  # type: ignore
async def button_user_filter(handler, event: CallbackQuery, data: MiddlewareData):
    if (
        data["callback_data"].user_id == event.from_user.id
        or event.from_user.id in data["app_cfg"].owners
    ):
        return await handler(event, data)

    await event.answer(data["i18n"].error.button_wrong_user(), cache_time=99999)


admin_f = MagicData(F.event_context.user_id.in_(F.app_cfg.owners))
admin_router.callback_query.filter(admin_f)
admin_router.inline_query.filter(admin_f)
admin_router.message.filter(admin_f)

commands_router.message.filter(~F.forward_origin & ~F.via_bot)
