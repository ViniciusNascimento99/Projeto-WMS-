"""Cria a estrutura inicial de autenticação do SIG-Log."""

from alembic import op

revision = "20261126_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE public.empresa (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            razao_social VARCHAR(255) NOT NULL,
            nome_fantasia VARCHAR(255),
            cnpj VARCHAR(14) NOT NULL,
            email VARCHAR(255) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'PENDENTE',
            criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),

            CONSTRAINT uq_empresa_cnpj UNIQUE (cnpj),
            CONSTRAINT ck_empresa_cnpj
                CHECK (cnpj ~ '^[0-9]{14}$'),
            CONSTRAINT ck_empresa_status
                CHECK (status IN ('PENDENTE', 'ATIVA', 'BLOQUEADA'))
        );

        CREATE TABLE public.perfil (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            nome VARCHAR(100) NOT NULL,
            descricao TEXT,
            empresa_id UUID,
            ativo BOOLEAN NOT NULL DEFAULT TRUE,
            criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),

            CONSTRAINT fk_perfil_empresa
                FOREIGN KEY (empresa_id)
                REFERENCES public.empresa(id)
                ON DELETE RESTRICT
        );

        CREATE UNIQUE INDEX uq_perfil_padrao_nome
        ON public.perfil (LOWER(nome))
        WHERE empresa_id IS NULL;

        CREATE UNIQUE INDEX uq_perfil_empresa_nome
        ON public.perfil (empresa_id, LOWER(nome))
        WHERE empresa_id IS NOT NULL;

        CREATE TABLE public.usuario (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            nome VARCHAR(150) NOT NULL,
            email VARCHAR(255) NOT NULL,
            senha_hash TEXT NOT NULL,
            empresa_id UUID NOT NULL,
            perfil_id UUID NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'ATIVO',
            criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),

            CONSTRAINT fk_usuario_empresa
                FOREIGN KEY (empresa_id)
                REFERENCES public.empresa(id)
                ON DELETE RESTRICT,

            CONSTRAINT fk_usuario_perfil
                FOREIGN KEY (perfil_id)
                REFERENCES public.perfil(id)
                ON DELETE RESTRICT,

            CONSTRAINT ck_usuario_status
                CHECK (status IN ('ATIVO', 'BLOQUEADO'))
        );

        CREATE UNIQUE INDEX uq_usuario_email_global
        ON public.usuario (LOWER(email));

        CREATE FUNCTION public.validar_perfil_usuario()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        AS $$
        DECLARE
            perfil_empresa UUID;
        BEGIN
            SELECT empresa_id
              INTO perfil_empresa
              FROM public.perfil
             WHERE id = NEW.perfil_id;

            IF NOT FOUND THEN
                RAISE EXCEPTION 'Perfil informado não existe.';
            END IF;

            IF perfil_empresa IS NOT NULL
               AND perfil_empresa <> NEW.empresa_id THEN
                RAISE EXCEPTION
                    'O perfil pertence a outra empresa.';
            END IF;

            RETURN NEW;
        END;
        $$;

        CREATE TRIGGER trg_validar_perfil_usuario
        BEFORE INSERT OR UPDATE OF perfil_id, empresa_id
        ON public.usuario
        FOR EACH ROW
        EXECUTE FUNCTION public.validar_perfil_usuario();

        CREATE FUNCTION public.validar_empresa_perfil()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        AS $$
        BEGIN
            IF NEW.empresa_id IS DISTINCT FROM OLD.empresa_id
               AND EXISTS (
                   SELECT 1
                     FROM public.usuario
                    WHERE perfil_id = OLD.id
               ) THEN
                RAISE EXCEPTION
                    'Não é permitido alterar a empresa de um perfil já utilizado.';
            END IF;

            RETURN NEW;
        END;
        $$;

        CREATE TRIGGER trg_validar_empresa_perfil
        BEFORE UPDATE OF empresa_id
        ON public.perfil
        FOR EACH ROW
        EXECUTE FUNCTION public.validar_empresa_perfil();

        CREATE FUNCTION public.atualizar_data_modificacao()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        AS $$
        BEGIN
            NEW.atualizado_em = NOW();
            RETURN NEW;
        END;
        $$;

        CREATE TRIGGER trg_empresa_atualizado_em
        BEFORE UPDATE ON public.empresa
        FOR EACH ROW
        EXECUTE FUNCTION public.atualizar_data_modificacao();

        CREATE TRIGGER trg_perfil_atualizado_em
        BEFORE UPDATE ON public.perfil
        FOR EACH ROW
        EXECUTE FUNCTION public.atualizar_data_modificacao();

        CREATE TRIGGER trg_usuario_atualizado_em
        BEFORE UPDATE ON public.usuario
        FOR EACH ROW
        EXECUTE FUNCTION public.atualizar_data_modificacao();
    """)


def downgrade() -> None:
    op.execute("""
        DROP TABLE IF EXISTS public.usuario;
        DROP TABLE IF EXISTS public.perfil;
        DROP TABLE IF EXISTS public.empresa;

        DROP FUNCTION IF EXISTS public.validar_empresa_perfil();
        DROP FUNCTION IF EXISTS public.validar_perfil_usuario();
        DROP FUNCTION IF EXISTS public.atualizar_data_modificacao();
    """)
