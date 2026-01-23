from __future__ import with_statement
from alembic import context
from sqlalchemy import engine_from_config, pool
from logging.config import fileConfig
import sys
import os

# --- Настройка путей ---
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from app import db  # импорт твоего Flask SQLAlchemy объекта
from app.models import *  # импорт всех моделей, чтобы Alembic их увидел

# --- Конфигурация Alembic ---
config = context.config
fileConfig(config.config_file_name)

# --- metadata от Flask SQLAlchemy ---
target_metadata = db.Model.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
