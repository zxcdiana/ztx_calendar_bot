import uvloop
import typer


def main():
    from app import database
    from app.scheduler import Scheduler
    from app.main import dp, bot, setup_logging
    from app import handlers

    database.register()
    dp["db"] = database.Database()
    dp["scheduler"] = Scheduler()
    setup_logging()
    handlers.register()

    uvloop.run(dp.start_polling(bot))


typer.run(main)
