def register():
    """Register handlers"""

    from app.handlers import filters, middlewares, eval, mood, common  # noqa: F401, F811
