# pyright: reportAssignmentType=false

import asyncio
import functools
import warnings

from telethon.sessions import SQLiteSession

warnings.filterwarnings(
    message="Using async sessions support is an experimental feature", action="ignore"
)


def wrap(func):
    @functools.wraps(func)
    async def wrapped(self: AsyncSQLiteSession, *a, **kw):
        async with self._lock:
            return await asyncio.to_thread(func, self, *a, **kw)

    return wrapped


class AsyncSQLiteSession(SQLiteSession):
    def __init__(self, session_id=None, store_tmp_auth_key_on_disk: bool = False):
        super().__init__(session_id, store_tmp_auth_key_on_disk)
        self._lock = asyncio.Lock()

    process_entities = wrap(SQLiteSession.process_entities)
