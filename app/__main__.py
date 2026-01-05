import uvloop

from app.database import Database
from app.scheduler import Scheduler
from app.main import dp, bot, setup_logging


setup_logging()


dp["db"] = Database()
dp["scheduler"] = Scheduler()

import app.handlers  # noqa: E402, F401


uvloop.run(dp.start_polling(bot))
