
from app.main import bot
async def test(*a):
    await bot.send_message(*a)
