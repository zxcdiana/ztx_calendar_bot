import asyncio
import re
from typing import cast
from contextlib import asynccontextmanager, suppress
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from geopy import Nominatim, Location
from geopy.adapters import AioHTTPAdapter

from timezonefinder.global_functions import timezone_at, _get_tf_instance

from app.utils import Singleton


_get_tf_instance()


class Geolocator(metaclass=Singleton):
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._unlock_time = 0
        self.ratelimit = 2

    @property
    def user_agent(self):
        return "ztx_calendar_bot"

    @property
    @asynccontextmanager
    async def lock(self):
        async with self._lock:
            loop = asyncio.get_running_loop()
            wait_before = self._unlock_time - loop.time()
            if wait_before > 0:
                await asyncio.sleep(wait_before)

            yield

            self._unlock_time = loop.time() + self.ratelimit

    def normalize_query(self, query: str):
        query = re.sub(r"[^\w\s\-]|[_\d]+", " ", query, flags=re.UNICODE)
        query = re.sub(r"\s+", " ", query).strip()
        return query.lower() or None

    async def get_timezone(self, raw_query: str):
        with suppress(ZoneInfoNotFoundError):
            ZoneInfo(raw_query)
            return raw_query

        query = self.normalize_query(raw_query)
        if query is None:
            return None

        async with (
            self.lock,
            Nominatim(
                user_agent=self.user_agent, adapter_factory=AioHTTPAdapter
            ) as geolocator,
        ):
            location = cast(
                Location | None,
                await geolocator.geocode(query),  # type: ignore
            )

        if location is None:
            return

        timezone = timezone_at(lng=location.longitude, lat=location.latitude)

        if timezone is not None:
            return timezone
