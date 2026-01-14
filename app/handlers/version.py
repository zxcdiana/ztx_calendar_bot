from __future__ import annotations

from aiogram import F
from aiogram.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.filters import Command

from app.main import commands_router
from app.meta import AppMetadata
from app.i18n import I18nContext


@commands_router.message(Command("version", "ver", "v", magic=~F.args))
async def version_command(m: Message, app_metadata: AppMetadata, i18n: I18nContext):
    method = m.answer if m.chat.type == "private" else m.reply
    await method(
        text=i18n.command_version.panel(
            homepage=app_metadata.homepage,
            name=app_metadata.name,
            description=app_metadata.description,
            version=app_metadata.version,
        ),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=i18n.command_version.button_source(),
                        url=app_metadata.homepage,
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text=i18n.command_version.button_starplz(),
                        url=app_metadata.homepage,
                    ),
                ],
            ]
        ),
    )
