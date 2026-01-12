.PHONY: unknown stub f up down build logs start stop restart purge reup

unknown:
	@echo "Unknown action. Exiting"

stub:
	@uv run ftl stub ./locales/ ./app/_stub.pyi

f:
	@ruff format && ruff check --fix && ruff format

up:
	@echo "--- Initialiazing database ..."
	@docker compose run --rm bot uv run alembic upgrade head
	@echo "--- [OK] Database initialized"
	@echo "--- Starting bot ..."
	@docker compose up -d
	@echo "--- [OK] Bot started"
	@$(MAKE) logs

down:
	@docker compose down

build:
	@docker compose build

logs:
	-@docker compose logs -f

start:
	@docker compose start
	@$(MAKE) logs

stop:
	@docker compose stop

restart:
	@docker compose restart
	@$(MAKE) logs

purge:
	@docker compose down --rmi=local

reup:
	@$(MAKE) purge
	@$(MAKE) up

dev:
	@uv run -m app --dev
