"""Repositório PostgreSQL de produtos."""

from src.infrastructure.postgres.connection import get_connection


class PostgresProductRepository:

    def create(self, sku: str, description: str, unit: str) -> dict:
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
