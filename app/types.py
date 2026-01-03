from pydantic import BaseModel
import pytz


class UserConfig(BaseModel):
    user_id: int
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    locale: str | None = None
    timezone: str | None = None

    @property
    def tz(self):
        return pytz.timezone(self.timezone or "asia/almaty")

    @property
    def lang_code(self) -> str:
        return self.locale or "ru"
