import logging


def setup_logging():
    logging.basicConfig(level=logging.INFO)


core = logging.getLogger("ztx_calendar_bot.core")
database = logging.getLogger("ztx_calendar_bot.database")
