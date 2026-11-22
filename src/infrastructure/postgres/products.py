"""Repositório PostgreSQL de produtos."""

import psycopg

from src.domain.errors import DomainError
from src.infrastructure.postgres.connection import get_connection


class PostgresProductRepository:

    def create(self, sku: str, description: str, unit: str) -> dict:
        try:
            with get_connection() as conn:
                row = conn.execute(
                    """
                    INSERT INTO produto (sku, descricao, unidade)
                    VALUES (%s, %s, %s)
                    RETURNING id, sku, descricao, unidade
                    """,
                    (sku, description, unit),
                ).fetchone()

                return {
                    "id": str(row[0]),
                    "sku": row[1],
                    "description": row[2],
                    "unit": row[3],
                }

        except psycopg.errors.UniqueViolation as exc:
            if exc.diag.constraint_name == "produto_sku_key":
                raise DomainError(
                    "SKU_ALREADY_EXISTS",
                    f"Product SKU {sku} already exists",
                ) from exc
            raise

    def get_by_id(self, product_id: str) -> dict | None:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT id, sku, descricao, unidade
                FROM produto
                WHERE id = %s
                """,
                (product_id,),
            ).fetchone()

            if row is None:
                return None

            return {
                "id": str(row[0]),
                "sku": row[1],
                "description": row[2],
                "unit": row[3],
            }
