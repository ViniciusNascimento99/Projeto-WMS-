"""Cria uma empresa pendente de aprovação e seu usuário administrador."""
import os
import re
import sys
from getpass import getpass

import psycopg
from pwdlib import PasswordHash


razao = input("Razão social: ").strip()
cnpj = re.sub(r"\D", "", input("CNPJ (14 dígitos): "))
nome = input("Nome do administrador: ").strip()
email = input("E-mail: ").strip().lower()
senha = getpass("Senha (mín. 8 caracteres): ")

if len(cnpj) != 14:
    raise SystemExit("CNPJ deve ter exatamente 14 dígitos.")
if not razao or not nome:
    raise SystemExit("Razão social e nome são obrigatórios.")
if "@" not in email:
    raise SystemExit("E-mail inválido.")
if len(senha) < 8:
    raise SystemExit("A senha deve ter pelo menos 8 caracteres.")

database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise SystemExit("Configure DATABASE_URL antes de executar o script.")

senha_hash = PasswordHash.recommended().hash(senha)

try:
    with psycopg.connect(database_url) as conn:
        empresa_id = conn.execute(
            """INSERT INTO public.empresa (razao_social, cnpj, email, status)
               VALUES (%s, %s, %s, 'PENDENTE')
               RETURNING id""",
            (razao, cnpj, email),
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
            (nome, email, senha_hash, empresa_id, perfil_id),
        )

except psycopg.errors.UniqueViolation as exc:
    if exc.diag.constraint_name == "uq_empresa_cnpj":
        mensagem = "Este CNPJ já está cadastrado."
    elif exc.diag.constraint_name == "uq_usuario_email_global":
        mensagem = "Este e-mail já está cadastrado."
    else:
        mensagem = "Já existe um cadastro com esses dados."
    raise SystemExit(mensagem) from None

print("Empresa e administrador criados.")
print("Status da empresa: PENDENTE — aguardando aprovação.")
