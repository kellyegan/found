from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel
from alembic import context

# Import all models so SQLModel.metadata is fully populated before autogenerate
# or migrations run. New models must be added here.
import app.models.image          # noqa: F401
import app.models.job            # noqa: F401
import app.models.tag            # noqa: F401
import app.models.category       # noqa: F401
import app.models.collection     # noqa: F401
import app.models.import_result  # noqa: F401

from app.core.config import settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def _db_url() -> str:
    # Allow the test suite (and CLI) to override via set_main_option.
    override = config.get_main_option("sqlalchemy.url")
    return override if override else settings.database_url


def run_migrations_offline() -> None:
    context.configure(
        url=_db_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    cfg = config.get_section(config.config_ini_section, {})
    cfg["sqlalchemy.url"] = _db_url()
    connectable = engine_from_config(
        cfg,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args={"check_same_thread": False},
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
