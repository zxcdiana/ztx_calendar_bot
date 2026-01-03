FROM ghcr.io/astral-sh/uv:0.9.18-python3.14-bookworm-slim

RUN useradd -m -s /bin/bash user
USER user
WORKDIR /home/user
COPY --chown=user:user . ztx_calendar_bot

CMD [ "uv", "run", "-m", "app" ]