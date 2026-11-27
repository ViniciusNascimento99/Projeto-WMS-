from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, HTTPException, status

from src.config.security import require_auth
from src.infrastructure.postgres.connection import get_connection


@dataclass(frozen=True, slots=True)
class RequestContext:
    usuario_id: str
    empresa_id: str
    perfil_id: str


def get_request_context(
    payload: dict = Depends(require_auth),
) -> RequestContext:
    try:
        usuario_id = UUID(payload["sub"])
        empresa_id = UUID(payload["empresa_id"])
    except (ValueError, TypeError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identificação inválida no token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT
                u.id,
                u.empresa_id,
                u.perfil_id,
                u.status,
                e.status,
                p.ativo
            FROM public.usuario u
            JOIN public.empresa e ON e.id = u.empresa_id
            JOIN public.perfil p ON p.id = u.perfil_id
            WHERE u.id = %s
              AND u.empresa_id = %s
            """,
            (usuario_id, empresa_id),
        ).fetchone()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não autorizado para esta empresa",
            headers={"WWW-Authenticate": "Bearer"},
        )

    uid, eid, perfil_id, usuario_status, empresa_status, perfil_ativo = row

    if usuario_status != "ATIVO" or empresa_status != "ATIVA" or not perfil_ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário, empresa ou perfil sem acesso ativo",
        )

    return RequestContext(
        usuario_id=str(uid),
        empresa_id=str(eid),
        perfil_id=str(perfil_id),
    )
