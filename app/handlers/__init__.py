# ruff: noqa: F401, F811


def register():
    """Register handlers"""

    from app.handlers import (
        filters,
        middlewares,
        eval,
        mood,
        common,
        start,
        emoji,
        user_config,
        version,
    )

    common.Handler.register_all()
