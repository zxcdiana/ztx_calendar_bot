
# Linux Installation
1. Create `.env` file and fill `BOT_TOKEN`, `OWNERS` and `POSTGRES_URL` fields
2. Init database:
```bash
uv run alembic upgrade head
```
3. Run bot:
```bash
uv run -m app
```

------------

# Docker installation
1. Create `.env` file and fill `BOT_TOKEN` and `OWNERS` fields

### With make:
```bash
make up
```

### Without make:
```bash
docker compose run --rm bot uv run alembic upgrade head && \
docker compose up -d && \
docker compose logs -f
```

------------

# `.env` file fields
- BOT_TOKEN: `str` — Token of telegram bot

- OWNERS: `list[int]` — Telegram user IDs of bot owners

- POSTGRES_URL: `str` — URL to PostgreSQL database (format: `postgresql://<USER>:<PASSWORD>@<HOST>/<DATABASE>`)
