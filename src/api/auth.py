"""Login por e-mail e senha: valida no Postgres e emite o JWT usado pelo require_auth."""
import os
from datetime import datetime, timedelta, timezone

import jwt
import psycopg
from fastapi import APIRouter, HTTPException
from pwdlib import PasswordHash
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])

_hasher = PasswordHash.recommended()
_DUMMY_HASH = _hasher.hash("senha-ficticia")  # evita revelar se o e-mail existe pelo tempo de resposta
TOKEN_HORAS = int(os.getenv("JWT_EXPIRES_HOURS", "8"))

SQL = """
    SELECT u.id, u.nome, u.email, u.senha_hash, u.status, u.empresa_id,
           e.status, p.nome
      FROM public.usuario u
      JOIN public.empresa e ON e.id = u.empresa_id
      JOIN public.perfil  p ON p.id = u.perfil_id
     WHERE LOWER(u.email) = LOWER(%s)
"""


class LoginIn(BaseModel):
    email: str
    senha: str


def _credenciais_invalidas() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail="E-mail ou senha inválidos",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.post("/login")
def login(dados: LoginIn):
    secret = os.getenv("JWT_SECRET")
    database_url = os.getenv("DATABASE_URL")
    if not secret or not database_url:
        raise HTTPException(status_code=500, detail="Autenticação não configurada")

    with psycopg.connect(database_url) as conn:
        row = conn.execute(SQL, (dados.email.strip(),)).fetchone()

    if row is None:
        _hasher.verify(dados.senha, _DUMMY_HASH)
        raise _credenciais_invalidas()

    uid, nome, email, senha_hash, u_status, empresa_id, e_status, perfil = row

    if not _hasher.verify(dados.senha, senha_hash):
        raise _credenciais_invalidas()
    if u_status != "ATIVO" or e_status != "ATIVA":
        raise HTTPException(status_code=403, detail="Usuário ou empresa sem acesso ativo")

    exp = datetime.now(timezone.utc) + timedelta(hours=TOKEN_HORAS)
    token = jwt.encode(
        {"sub": str(uid), "empresa_id": str(empresa_id), "perfil": perfil, "exp": exp},
        secret,
        algorithm="HS256",
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": TOKEN_HORAS * 3600,
        "usuario": {"id": str(uid), "nome": nome, "email": email, "perfil": perfil},
    }


# ---------- Primeiro acesso (cadastro do administrador pela tela) ----------
import re


class RegistroIn(BaseModel):
    razao_social: str
    cnpj: str
    nome: str
    email: str
    senha: str


def _url_banco() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise HTTPException(status_code=500, detail="Banco não configurado")
    return url


@router.get("/status")
def status_cadastro():
    try:
        with psycopg.connect(_url_banco()) as conn:
            total = conn.execute("SELECT COUNT(*) FROM public.usuario").fetchone()[0]
    except psycopg.errors.UndefinedTable:
        raise HTTPException(status_code=503, detail="Tabelas não criadas: rode a migration")
    return {"precisa_cadastro": total == 0}


@router.post("/registrar", status_code=201)
def registrar_empresa(dados: RegistroIn):
    cnpj = re.sub(r"\\D", "", dados.cnpj)
    email = dados.email.strip().lower()

    if len(cnpj) != 14:
        raise HTTPException(status_code=422, detail="CNPJ deve ter 14 dígitos")
    if "@" not in email:
        raise HTTPException(status_code=422, detail="E-mail inválido")
    if len(dados.senha) < 8:
        raise HTTPException(status_code=422, detail="A senha deve ter pelo menos 8 caracteres")
    if not dados.razao_social.strip() or not dados.nome.strip():
        raise HTTPException(status_code=422, detail="Preencha razão social e nome")

    senha_hash = _hasher.hash(dados.senha)

    try:
        with psycopg.connect(_url_banco()) as conn:
            empresa_id = conn.execute(
                """INSERT INTO public.empresa (razao_social, cnpj, email, status)
                   VALUES (%s, %s, %s, 'PENDENTE')
                   RETURNING id""",
                (dados.razao_social.strip(), cnpj, email),
            ).fetchone()[0]

            row = conn.execute(
                """SELECT id FROM public.perfil
                   WHERE empresa_id IS NULL AND LOWER(nome) = 'administrador'"""
            ).fetchone()

            perfil_id = row[0] if row else conn.execute(
                """INSERT INTO public.perfil (nome, descricao)
                   VALUES ('Administrador', 'Acesso total')
                   RETURNING id"""
            ).fetchone()[0]

            conn.execute(
                """INSERT INTO public.usuario
                   (nome, email, senha_hash, empresa_id, perfil_id)
                   VALUES (%s, %s, %s, %s, %s)""",
                (dados.nome.strip(), email, senha_hash, empresa_id, perfil_id),
            )

    except psycopg.errors.UniqueViolation as exc:
        constraint = exc.diag.constraint_name

        if constraint == "uq_empresa_cnpj":
            mensagem = "Este CNPJ já está cadastrado."
        elif constraint == "uq_usuario_email_global":
            mensagem = "Este e-mail já está cadastrado."
        else:
            mensagem = "Já existe um cadastro com esses dados."

        raise HTTPException(status_code=409, detail=mensagem) from exc

    return {
        "mensagem": "Cadastro recebido. A empresa aguarda aprovação do administrador da plataforma."
    }
