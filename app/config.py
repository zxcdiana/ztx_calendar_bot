from __future__ import annotations

from pathlib import Path
import re
from typing import Literal

from pydantic import AliasChoices, Field, Secret, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    owners: set[int]
    bot_token: Secret[str]
    api_id: Secret[int] | None = None
    api_hash: Secret[str] | None = None
    postgres_url: Secret[str] = Field(
        validation_alias=AliasChoices("_compose_postgres_url")
    )
    locale: Literal["ru"] = "ru"

    model_config = SettingsConfigDict(
        extra="ignore", frozen=True, populate_by_name=True
    )

    @field_validator("postgres_url", mode="after")
    @classmethod
    def _postgres_url_validator(cls, value: Secret[str]):
        if not re.fullmatch(
            r"postgres(ql|)://(?P<user>.+?):(?P<password>.+?)@(?P<host>.+?)/(?P<db>.+?)",
            value.get_secret_value(),
        ):
            raise ValueError(
                "Invalid `postgres_url`."
                "Value has been in format: `postgresql://<USER>:<PASSWORD>@<HOST>/<DATABASE>`"
            )
        return value

    def get_db_uri(self, /, mode: Literal["sync", "async"]):
        uri = self.postgres_url.get_secret_value()
        uri = uri[len(re.match(r"postgres(ql|)://", uri)[0]) :]  # pyright: ignore[reportOptionalSubscript]
        if mode == "sync":
            return f"postgresql+psycopg2://{uri}"
        elif mode == "async":
            return f"postgresql+asyncpg://{uri}"
        else:
            raise ValueError(f"invalid mode: {mode}")


def get_app_config(*, env_file: str | Path | None = None):
    if env_file is None:
        env_file = ".env"
    return AppConfig(_env_file=env_file)  # pyright: ignore[reportCallIssue]
