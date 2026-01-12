import sqlalchemy as sa

from aiogram import F
from aiogram.types import Message
from aiogram.filters import Command

from app import utils
from app.main import admin_router

from app.handlers.common import Handler


logger = utils.get_logger()


class SqlCommand(Handler[Message]):
    @classmethod
    def register(cls) -> None:
        admin_router.message.register(cls, Command("sql", magic=F.args))

    async def handle(self):
        async with self.data["db"].begin() as session:
            try:
                result = await session.execute(sa.text(self.data["command"].args))
            except Exception as e:
                logger.exception("")
                result = f"err: {e}"
            else:
                result = result.all()

        if len(result) == 1:
            result = result[0]

        await self.event.reply(
            f"<blockquote expandable>{utils.escape_html(str(result)[:2000])}</blockquote>"
        )
