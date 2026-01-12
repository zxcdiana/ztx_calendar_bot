from logging.config import fileConfig
import os

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

from app.config import get_app_config
from app._database.orm import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata


def get_postgres_url():
    x_args = context.get_x_argument(as_dictionary=True)
    env_file = None

    env_file_from_env = os.getenv('ALEMBIC_ENV_FILE')
    env_file_from_args = x_args.get('env-file') or x_args.get('env_file') or x_args.get('ef')
    url_from_env = os.getenv('ALEMBIC_URL')
    url_from_args = x_args.get('url')

    if env_file_from_args:
        env_file = env_file_from_args
    elif env_file_from_env:
        env_file = env_file_from_env
    elif url_from_args:
        return url_from_args
    elif url_from_env:
        return url_from_env
    
    return get_app_config(env_file=env_file).get_db_uri(mode='sync')

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.
config.set_main_option("sqlalchemy.url", get_postgres_url())




def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def online_include_name(name, type_, parent_names):
    match type_, name:
        case 'table', 'apscheduler_jobs':
            return False
    return True

def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata, 
            include_name=online_include_name
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
