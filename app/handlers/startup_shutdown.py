from aiogram import Bot
from app.routers import main_router


@main_router.startup()
async def drop_updates(bots: list[Bot]):
    for bot in bots:
        await bot.delete_webhook(drop_pending_updates=True)
