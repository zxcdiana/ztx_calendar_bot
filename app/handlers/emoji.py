import json
from pathlib import Path
from typing import TypeAlias

from aiogram.types import Message
from aiogram.filters import Command

import grapheme

from app import utils
from app.main import commands_router


Emoji: TypeAlias = str
CustomEmojiId: TypeAlias = int

emojis: dict[Emoji, CustomEmojiId] = json.loads(
    (Path(__file__).parent / "custom_emojis.json").read_bytes()
)


@commands_router.message(Command("emj", "emoji"))
async def emoji_command(m: Message):
    text = ""
    for emoji in grapheme.graphemes(m.text):
        if emoji in emojis:
            text += f"<code>{utils.escape_html(f"<tg-emoji emoji-id='{emojis[emoji]}'>{emoji}</tg-emoji>")}</code>\n"
    if text:
        await m.reply(text)
