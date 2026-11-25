"""Configuração do ambiente de migrações do Alembic."""

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool
from sqlalchemy.engine import make_url

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# As migrações serão escritas em SQL explícito.
target_metadata = None

# Hosts locais autorizados por padrão.
LOCAL_DATABASE_HOSTS = {
    "localhost",
    "127.0.0.1",
    "::1",
    "postgres",
}


def get_database_url() -> str:
    """Obtém e valida a URL do banco de dados."""

    database_url = os.environ.get("DATABASE_URL", "").strip()

    if not database_url:
        raise RuntimeError(
            "A variável DATABASE_URL não está configurada."
        )

    url = make_url(database_url)
    database_host = (url.host or "").lower()

    allow_remote = (
        os.environ.get("ALEMBIC_ALLOW_REMOTE", "").lower() == "true"
    )

    if database_host not in LOCAL_DATABASE_HOSTS and not allow_remote:
        raise RuntimeError(
            "Migração bloqueada: o banco de dados é remoto. "
            "Para autorizar explicitamente, configure "
            "ALEMBIC_ALLOW_REMOTE=true."
        )

    return url.set(
        drivername="postgresql+psycopg"
    ).render_as_string(hide_password=False)


def run_migrations_offline() -> None:
    """Gera SQL das migrações sem conectar ao banco."""

    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema="public",
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Executa migrações utilizando uma conexão PostgreSQL."""

    connectable = create_engine(
        get_database_url(),
        poolclass=pool.NullPool,
        connect_args={"options": "-csearch_path=public,wms"},
    )

    try:
        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                version_table_schema="public",
            )

            with context.begin_transaction():
                context.run_migrations()
    finally:
        connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
