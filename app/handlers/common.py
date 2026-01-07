from aiogram.types import Message, CallbackQuery

from app.handlers.callback_data import DeleteMessage, empty_callback_data
from app.main import main_router


@main_router.callback_query(DeleteMessage.filter())
async def delete_message(call: CallbackQuery):
    m = call.message
    if not isinstance(m, Message):
        await call.answer(f"unknown: {type(call.message).__name__}")
        return

    try:
        if m.text:
            await m.edit_text(inline_message_id=call.inline_message_id, text="\xad")
        elif m.caption:
            await m.edit_caption(
                inline_message_id=call.inline_message_id, caption="\xad"
            )
    finally:
        await m.delete()


@main_router.callback_query(empty_callback_data.filter())
async def handle_empty_button(call: CallbackQuery):
    await call.answer(cache_time=99999)
