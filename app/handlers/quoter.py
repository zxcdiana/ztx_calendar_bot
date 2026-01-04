import random
from typing import Any, Iterable
from aiogram import F
import aiohttp
from pydantic import BaseModel
from yarl import URL
from app import utils
from app.main import main_router
from aiogram.types import Message, BufferedInputFile, ChatFullInfo

logger = utils.get_logger()


class Quoter:
    def __init__(self, api_url: str) -> None:
        self.api = URL(api_url)

    async def quote(self, messages: Message | Iterable[Message]) -> BufferedInputFile:
        if isinstance(messages, Message):
            messages = (messages,)

        data = {"messages": [await self.pack_message(m) for m in messages]}
        logger.info(f"qu: {data=}")
        async with (
            aiohttp.ClientSession() as session,
            session.post(self.api / "generate.webp", json=data) as response,
        ):
            response.raise_for_status()
            return BufferedInputFile(
                await response.content.read(), filename="quote.webp"
            )

    @classmethod
    async def pack_message(cls, m: Message) -> dict[str, Any]:
        data = {
            "avatar": True,
            "text": m.text or m.caption,
            "entities": m.entities or m.caption_entities,
            "from": await cls.pack_sender(await m.bot.get_chat(m.from_user.id)),
        }
        if reply := m.reply_to_message:
            data.update(
                {
                    "reply_to_message": {
                        "name": reply.from_user.full_name if reply.from_user else None,
                        "text": reply.text or reply.caption,
                        "entities": reply.text or reply.entities,
                        "chatId": reply.chat.id,
                        "from": await cls.pack_sender(
                            await reply.bot.get_chat(reply.from_user.id)
                        )
                        if reply.from_user
                        else None,
                    }
                }
            )
        if media := await cls._pack_media(m):
            data.update(media)

        return data

    @classmethod
    async def _pack_media(cls, m: Message) -> dict[str, Any]:
        if m.voice:
            waveform = [random.randint(0, 30) for _ in range(500)]
            return {"voice": {"waveform": waveform}}

        if m.photo:
            return {"media": list(x.model_dump(exclude_none=True) for x in m.photo)}

        media = getattr(m, m.content_type)
        for attr in {"thumb", "thumbnail"}:
            if value := getattr(media, attr, None):
                if issubclass(type(value), BaseModel):
                    value = value.model_dump(exclude_none=True)
                if value:
                    return {"media": value}

        return {}

    @classmethod
    async def pack_sender(cls, chat: ChatFullInfo) -> dict[str, Any]:
        return {
            "id": chat.id,
            "name": chat.full_name,
            "username": chat.username,
            "photo": {"big_file_id": chat.photo.big_file_id if chat.photo else None},
            "emoji_status": chat.emoji_status_custom_emoji_id,
        }


quoter = Quoter("http://127.0.0.1:3000")


@main_router.message(F.content_type != "text")
async def quote(m: Message):
    file = await quoter.quote(m)
    await m.reply_sticker(file)
