from aiogram import F
from aiogram.types import CallbackQuery
from aiogram.filters import MagicData

from app.config import app_cfg
from app.routers import main_router, commands_router
from app.handlers.callback_data import CallbackData
from app.i18n import I18nContext


@main_router.callback_query.filter
async def button_user_filter(
    call: CallbackQuery, callback_data: CallbackData, i18n: I18nContext
):
    if (
        callback_data.user_id == call.from_user.id
        or call.from_user.id in app_cfg.owners
    ):
        return True

    await call.answer(i18n.error.button_wrong_user(), cache_time=99999)


admin_f = MagicData(F.event_context.user_id.in_(app_cfg.owners))
main_router.callback_query.filter(admin_f)
main_router.inline_query.filter(admin_f)
main_router.message.filter(admin_f)

commands_router.message.filter(~F.forward_origin & ~F.via_bot)
