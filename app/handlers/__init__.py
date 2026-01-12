def register():
    """Register handlers"""

    from app.handlers import filters, middlewares, eval, mood, common, start, sql  # noqa: F401, F811

    common.Handler.register_all()
