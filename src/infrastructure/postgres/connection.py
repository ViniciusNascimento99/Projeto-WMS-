"""Gerencia conexões com o PostgreSQL."""
import os

import psycopg


def get_connection():
    """Abre uma conexão com o banco PostgreSQL."""
    database_url = os.environ.get("DATABASE_URL", "").strip()

    if not database_url:
        raise RuntimeError("A variável DATABASE_URL não está configurada.")

    return psycopg.connect(
        database_url,
        options="-csearch_path=wms",
    )
