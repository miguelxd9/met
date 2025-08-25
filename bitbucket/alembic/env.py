"""
Alembic environment configuration for Bitbucket DevOps Metrics

This file configures the Alembic environment for database migrations.
"""

import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, create_engine
from alembic import context

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the models to ensure they are registered with SQLAlchemy
from src.models import Base
from src.config.settings import get_settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_database_url():
    """Get database URL from environment or settings"""
    # First try to get from environment variable
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        # Fall back to settings
        try:
            settings = get_settings()
            database_url = settings.database_url
        except Exception:
            # Default fallback
            database_url = "postgresql://usuario:password@localhost:5432/bitbucket_metrics"
    
    # Forzar el uso de psycopg en lugar de psycopg2
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://")
    
    return database_url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Get database URL
    database_url = get_database_url()
    
    # Update the config with the actual database URL
    config.set_main_option("sqlalchemy.url", database_url)
    
    # Crear engine con configuración específica para psycopg
    connectable = create_engine(
        database_url,
        poolclass=pool.NullPool,
        connect_args={
            "connect_timeout": 10,
            "options": "-c application_name=alembic_migration -c timezone=UTC"
        }
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
