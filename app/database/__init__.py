import inspect
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .database import Database
    from .models import UserConfig, MoodMonth
    from . import orm


__all__ = ("Database", "UserConfig", "MoodMonth", "orm")


def register():
    from .database import Database
    from .models import UserConfig, MoodMonth
    from . import orm

    module = inspect.getmodule(register)
    for obj in (Database, UserConfig, MoodMonth, orm):
        setattr(module, obj.__name__, obj)
