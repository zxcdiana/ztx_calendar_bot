from aiogram import Dispatcher, Router
from aiogram.fsm.storage.memory import SimpleEventIsolation


dp = Dispatcher(events_isolation=SimpleEventIsolation())
main_router = dp.include_router(Router())
commands_router = main_router.include_router(Router())
mood_router = commands_router.include_router(Router())
admin_router = commands_router.include_router(Router())
