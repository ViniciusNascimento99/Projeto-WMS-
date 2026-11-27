"""Cria estrutura operacional WMS.

Revision ID: 5dae80d669d0
Revises: 20261126_01
Create Date: 2026-11-26
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "5dae80d669d0"
down_revision: Union[str, Sequence[str], None] = "20261126_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Cria a estrutura operacional do WMS."""

    op.execute("CREATE SCHEMA IF NOT EXISTS wms")

    # Sequências auxiliares.
    op.execute("""
        CREATE SEQUENCE IF NOT EXISTS wms.seq_recebimento
        START WITH 1 INCREMENT BY 1
        NO MINVALUE NO MAXVALUE CACHE 1
    """)

    op.execute("""
        CREATE SEQUENCE IF NOT EXISTS wms.seq_embalagem
        START WITH 1 INCREMENT BY 1
        NO MINVALUE NO MAXVALUE CACHE 1
    """)

    op.execute("""
        CREATE SEQUENCE IF NOT EXISTS wms.seq_expedicao
        START WITH 1 INCREMENT BY 1
        NO MINVALUE NO MAXVALUE CACHE 1
    """)

    op.execute("""
        CREATE SEQUENCE IF NOT EXISTS wms.seq_picking
        START WITH 1 INCREMENT BY 1
        NO MINVALUE NO MAXVALUE CACHE 1
    """)

    # Centros de distribuição.
    op.execute("""
        CREATE TABLE IF NOT EXISTS wms.centro_distribuicao (
            id uuid DEFAULT gen_random_uuid() NOT NULL,
            codigo text NOT NULL,
            nome text NOT NULL,
            cidade text,
            uf character(2),
            ativo boolean DEFAULT true NOT NULL,
            criado_em timestamp with time zone DEFAULT now() NOT NULL,
            CONSTRAINT centro_distribuicao_pkey PRIMARY KEY (id),
            CONSTRAINT centro_distribuicao_codigo_key UNIQUE (codigo)
        )
    """)

    # Zonas do centro de distribuição.
    op.execute("""
        CREATE TABLE IF NOT EXISTS wms.zona (
            id uuid DEFAULT gen_random_uuid() NOT NULL,
            cd_id uuid NOT NULL,
            codigo text NOT NULL,
            nome text NOT NULL,
            tipo text NOT NULL,
            CONSTRAINT zona_tipo_check CHECK (
                tipo = ANY (ARRAY[
                    'RECEBIMENTO', 'ARMAZENAGEM', 'PICKING',
                    'PACKING', 'EXPEDICAO', 'QUARENTENA'
                ]::text[])
            ),
            CONSTRAINT zona_pkey PRIMARY KEY (id),
            CONSTRAINT zona_cd_id_codigo_key UNIQUE (cd_id, codigo),
            CONSTRAINT zona_id_cd_id_key UNIQUE (id, cd_id),
            CONSTRAINT zona_cd_id_fkey
                FOREIGN KEY (cd_id)
                REFERENCES wms.centro_distribuicao(id)
        )
    """)

    # Endereços físicos.
    op.execute("""
        CREATE TABLE IF NOT EXISTS wms.endereco (
            id uuid DEFAULT gen_random_uuid() NOT NULL,
            cd_id uuid NOT NULL,
            zona_id uuid NOT NULL,
            codigo text NOT NULL,
            corredor text,
            prateleira text,
            nivel integer,
            capacidade integer NOT NULL,
            ativo boolean DEFAULT true NOT NULL,
            criado_em timestamp with time zone DEFAULT now() NOT NULL,
            atualizado_em timestamp with time zone DEFAULT now() NOT NULL,
            CONSTRAINT endereco_capacidade_check CHECK (capacidade > 0),
            CONSTRAINT endereco_pkey PRIMARY KEY (id),
            CONSTRAINT endereco_cd_id_codigo_key UNIQUE (cd_id, codigo),
            CONSTRAINT endereco_zona_id_cd_id_fkey
                FOREIGN KEY (zona_id, cd_id)
                REFERENCES wms.zona(id, cd_id)
        )
    """)

    # Cargas.
    op.execute("""
        CREATE TABLE IF NOT EXISTS wms.carga (
            id uuid DEFAULT gen_random_uuid() NOT NULL,
            codigo text NOT NULL,
            cd_id uuid NOT NULL,
            coleta_externa_id text,
            origem text,
            status text DEFAULT 'PREVISTA'::text NOT NULL,
            criado_em timestamp with time zone DEFAULT now() NOT NULL,
            CONSTRAINT carga_status_check CHECK (
                status = ANY (
                    ARRAY['PREVISTA', 'CHEGOU', 'DESCARREGADA']::text[]
                )
            ),
            CONSTRAINT carga_pkey PRIMARY KEY (id),
            CONSTRAINT carga_codigo_key UNIQUE (codigo),
            CONSTRAINT carga_coleta_externa_id_key UNIQUE (coleta_externa_id),
            CONSTRAINT carga_cd_id_fkey
                FOREIGN KEY (cd_id)
                REFERENCES wms.centro_distribuicao(id)
        )
    """)

    # Produtos.
    op.execute("""
        CREATE TABLE IF NOT EXISTS wms.produto (
            id uuid DEFAULT gen_random_uuid() NOT NULL,
            sku text NOT NULL,
            descricao text NOT NULL,
            unidade text NOT NULL,
            peso_kg numeric(10,3),
            volume_m3 numeric(10,4),
            controla_lote boolean DEFAULT false NOT NULL,
            controla_validade boolean DEFAULT false NOT NULL,
            estoque_minimo integer DEFAULT 0 NOT NULL,
            estoque_maximo integer,
            ativo boolean DEFAULT true NOT NULL,
            criado_em timestamp with time zone DEFAULT now() NOT NULL,
            atualizado_em timestamp with time zone DEFAULT now() NOT NULL,
            CONSTRAINT produto_check CHECK (
                estoque_maximo IS NULL
                OR estoque_maximo >= estoque_minimo
            ),
            CONSTRAINT produto_estoque_minimo_check
                CHECK (estoque_minimo >= 0),
            CONSTRAINT produto_peso_kg_check
                CHECK (peso_kg >= 0::numeric),
            CONSTRAINT produto_volume_m3_check
                CHECK (volume_m3 >= 0::numeric),
            CONSTRAINT produto_pkey PRIMARY KEY (id),
            CONSTRAINT produto_sku_key UNIQUE (sku)
        )
    """)

    # Lotes.
    op.execute("""
        CREATE TABLE IF NOT EXISTS wms.lote (
            id uuid DEFAULT gen_random_uuid() NOT NULL,
            produto_id uuid NOT NULL,
            codigo text NOT NULL,
            validade date,
            criado_em timestamp with time zone DEFAULT now() NOT NULL,
            CONSTRAINT lote_pkey PRIMARY KEY (id),
            CONSTRAINT lote_produto_id_codigo_key UNIQUE (produto_id, codigo),
            CONSTRAINT lote_produto_id_fkey
                FOREIGN KEY (produto_id)
                REFERENCES wms.produto(id)
        )
    """)

    # Recebimentos.
    op.execute("""
        CREATE TABLE IF NOT EXISTS wms.recebimento (
            id uuid DEFAULT gen_random_uuid() NOT NULL,
            codigo text DEFAULT (
                'REC-'::text ||
                lpad(
                    (nextval('wms.seq_recebimento'::regclass))::text,
                    6,
                    '0'::text
                )
            ) NOT NULL,
            carga_id uuid NOT NULL,
            nota_fiscal text,
            status text DEFAULT 'AGUARDANDO'::text NOT NULL,
            conferido_em timestamp with time zone,
            conferido_por text,
            criado_em timestamp with time zone DEFAULT now() NOT NULL,
            atualizado_em timestamp with time zone DEFAULT now() NOT NULL,
            CONSTRAINT recebimento_status_check CHECK (
                status = ANY (ARRAY[
                    'AGUARDANDO', 'EM_CONFERENCIA', 'CONFERIDA',
                    'COM_DIVERGENCIA', 'ARMAZENADA'
                ]::text[])
            ),
            CONSTRAINT recebimento_pkey PRIMARY KEY (id),
            CONSTRAINT recebimento_carga_id_nota_fiscal_key
                UNIQUE (carga_id, nota_fiscal),
            CONSTRAINT recebimento_codigo_key UNIQUE (codigo),
            CONSTRAINT recebimento_carga_id_fkey
                FOREIGN KEY (carga_id)
                REFERENCES wms.carga(id)
        )
    """)

    # Itens dos recebimentos.
    op.execute("""
        CREATE TABLE IF NOT EXISTS wms.recebimento_item (
            id uuid DEFAULT gen_random_uuid() NOT NULL,
            recebimento_id uuid NOT NULL,
            produto_id uuid NOT NULL,
            lote_id uuid,
            qtd_esperada integer NOT NULL,
            qtd_conferida integer,
            divergencia boolean GENERATED ALWAYS AS (
                (qtd_conferida IS NOT NULL)
                AND (qtd_conferida <> qtd_esperada)
            ) STORED,
            CONSTRAINT recebimento_item_qtd_conferida_check
                CHECK (qtd_conferida >= 0),
            CONSTRAINT recebimento_item_qtd_esperada_check
                CHECK (qtd_esperada > 0),
            CONSTRAINT recebimento_item_pkey PRIMARY KEY (id),
            CONSTRAINT recebimento_item_recebimento_id_produto_id_lote_id_key
                UNIQUE NULLS NOT DISTINCT (recebimento_id, produto_id, lote_id),
            CONSTRAINT recebimento_item_lote_id_fkey
                FOREIGN KEY (lote_id)
                REFERENCES wms.lote(id),
            CONSTRAINT recebimento_item_produto_id_fkey
                FOREIGN KEY (produto_id)
                REFERENCES wms.produto(id),
            CONSTRAINT recebimento_item_recebimento_id_fkey
                FOREIGN KEY (recebimento_id)
                REFERENCES wms.recebimento(id)
                ON DELETE CASCADE
        )
    """)

    # Alocações.
    op.execute("""
        CREATE TABLE IF NOT EXISTS wms.alocacao (
            id uuid DEFAULT gen_random_uuid() NOT NULL,
            recebimento_item_id uuid NOT NULL,
            endereco_id uuid NOT NULL,
            quantidade integer NOT NULL,
            alocado_por text,
            alocado_em timestamp with time zone DEFAULT now() NOT NULL,
            CONSTRAINT alocacao_quantidade_check CHECK (quantidade > 0),
            CONSTRAINT alocacao_pkey PRIMARY KEY (id),
            CONSTRAINT alocacao_endereco_id_fkey
                FOREIGN KEY (endereco_id)
                REFERENCES wms.endereco(id),
            CONSTRAINT alocacao_recebimento_item_id_fkey
                FOREIGN KEY (recebimento_item_id)
                REFERENCES wms.recebimento_item(id)
        )
    """)

    # Estoque.
    op.execute("""
        CREATE TABLE IF NOT EXISTS wms.estoque (
            id uuid DEFAULT gen_random_uuid() NOT NULL,
            endereco_id uuid NOT NULL,
            produto_id uuid NOT NULL,
            lote_id uuid,
            quantidade integer DEFAULT 0 NOT NULL,
            quantidade_reservada integer DEFAULT 0 NOT NULL,
            atualizado_em timestamp with time zone DEFAULT now() NOT NULL,
            CONSTRAINT ck_reserva_menor_saldo
                CHECK (quantidade_reservada <= quantidade),
            CONSTRAINT estoque_quantidade_check CHECK (quantidade >= 0),
            CONSTRAINT estoque_quantidade_reservada_check
                CHECK (quantidade_reservada >= 0),
            CONSTRAINT estoque_pkey PRIMARY KEY (id),
            CONSTRAINT estoque_endereco_id_produto_id_lote_id_key
                UNIQUE NULLS NOT DISTINCT (endereco_id, produto_id, lote_id),
            CONSTRAINT estoque_endereco_id_fkey
                FOREIGN KEY (endereco_id)
                REFERENCES wms.endereco(id),
            CONSTRAINT estoque_lote_id_fkey
                FOREIGN KEY (lote_id)
                REFERENCES wms.lote(id),
            CONSTRAINT estoque_produto_id_fkey
                FOREIGN KEY (produto_id)
                REFERENCES wms.produto(id)
        )
    """)

    # Histórico de movimentações.
    op.execute("""
        CREATE TABLE IF NOT EXISTS wms.movimentacao_estoque (
            id bigint GENERATED ALWAYS AS IDENTITY (
                SEQUENCE NAME wms.movimentacao_estoque_id_seq
                START WITH 1
                INCREMENT BY 1
                NO MINVALUE
                NO MAXVALUE
                CACHE 1
            ) NOT NULL,
            produto_id uuid NOT NULL,
            endereco_id uuid NOT NULL,
            lote_id uuid,
            tipo text NOT NULL,
            delta integer NOT NULL,
            saldo_apos integer NOT NULL,
            motivo text,
            ref_tipo text,
            ref_id uuid,
            correlation_id text,
            criado_por text,
            criado_em timestamp with time zone DEFAULT now() NOT NULL,
            CONSTRAINT ck_tipo_sinal CHECK (
                (
                    (tipo = 'ENTRADA'::text AND delta > 0)
                    OR (tipo = 'SAIDA'::text AND delta < 0)
                    OR tipo = 'AJUSTE'::text
                )
            ),
            CONSTRAINT movimentacao_estoque_delta_check CHECK (delta <> 0),
            CONSTRAINT movimentacao_estoque_ref_tipo_check CHECK (
                ref_tipo = ANY (ARRAY[
                    'ALOCACAO', 'PICKING', 'EXPEDICAO',
                    'INVENTARIO', 'AJUSTE_MANUAL'
                ]::text[])
            ),
            CONSTRAINT movimentacao_estoque_saldo_apos_check
                CHECK (saldo_apos >= 0),
            CONSTRAINT movimentacao_estoque_tipo_check CHECK (
                tipo = ANY (ARRAY['ENTRADA', 'SAIDA', 'AJUSTE']::text[])
            ),
            CONSTRAINT movimentacao_estoque_pkey PRIMARY KEY (id),
            CONSTRAINT movimentacao_estoque_endereco_id_fkey
                FOREIGN KEY (endereco_id)
                REFERENCES wms.endereco(id),
            CONSTRAINT movimentacao_estoque_lote_id_fkey
                FOREIGN KEY (lote_id)
                REFERENCES wms.lote(id),
            CONSTRAINT movimentacao_estoque_produto_id_fkey
                FOREIGN KEY (produto_id)
                REFERENCES wms.produto(id)
        )
    """)

    # Índices auxiliares.
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_alocacao_item
        ON wms.alocacao USING btree (recebimento_item_id)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_endereco_zona
        ON wms.endereco USING btree (zona_id)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_estoque_produto
        ON wms.estoque USING btree (produto_id)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_mov_endereco
        ON wms.movimentacao_estoque USING btree (endereco_id)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_mov_produto_data
        ON wms.movimentacao_estoque USING btree (produto_id, criado_em DESC)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_recebimento_status
        ON wms.recebimento USING btree (status)
    """)



    # Isolamento multiempresa.
    # A migration não atribui empresas arbitrariamente a registros antigos.
    op.execute("""
        DO $$
        DECLARE
            tabela text;
            possui_dados boolean;
        BEGIN
            FOREACH tabela IN ARRAY ARRAY[
                'centro_distribuicao',
                'zona',
                'endereco',
                'carga',
                'produto',
                'lote',
                'recebimento',
                'recebimento_item',
                'alocacao',
                'estoque',
                'movimentacao_estoque'
            ]
            LOOP
                EXECUTE format(
                    'SELECT EXISTS (SELECT 1 FROM wms.%I LIMIT 1)',
                    tabela
                ) INTO possui_dados;

                IF possui_dados THEN
                    RAISE EXCEPTION
                        'Migration multiempresa interrompida: wms.% possui registros. '
                        'É necessário definir a empresa responsável antes da migração.',
                        tabela;
                END IF;
            END LOOP;
        END
        $$;
    """)

    # Adiciona empresa_id a todas as tabelas operacionais.
    tabelas = [
        "centro_distribuicao",
        "zona",
        "endereco",
        "carga",
        "produto",
        "lote",
        "recebimento",
        "recebimento_item",
        "alocacao",
        "estoque",
        "movimentacao_estoque",
    ]

    for tabela in tabelas:
        op.execute(
            f"ALTER TABLE wms.{tabela} "
            "ADD COLUMN IF NOT EXISTS empresa_id uuid"
        )
        op.execute(
            f"ALTER TABLE wms.{tabela} "
            "ALTER COLUMN empresa_id SET NOT NULL"
        )
        op.execute(
            f"""
            ALTER TABLE wms.{tabela}
            ADD CONSTRAINT fk_{tabela}_empresa
            FOREIGN KEY (empresa_id)
            REFERENCES public.empresa(id)
            """
        )

    # Remove unicidades globais que passam a ser por empresa.
    op.execute("""
        ALTER TABLE wms.centro_distribuicao
        DROP CONSTRAINT IF EXISTS centro_distribuicao_codigo_key;

        ALTER TABLE wms.produto
        DROP CONSTRAINT IF EXISTS produto_sku_key;

        ALTER TABLE wms.carga
        DROP CONSTRAINT IF EXISTS carga_codigo_key;

        ALTER TABLE wms.carga
        DROP CONSTRAINT IF EXISTS carga_coleta_externa_id_key;

        ALTER TABLE wms.recebimento
        DROP CONSTRAINT IF EXISTS recebimento_codigo_key;
    """)

    # Chaves únicas compostas para permitir referências seguras entre empresas.
    constraints_unicas = {
        "centro_distribuicao": "uq_wms_cd_id_empresa",
        "zona": "uq_wms_zona_id_empresa",
        "endereco": "uq_wms_endereco_id_empresa",
        "carga": "uq_wms_carga_id_empresa",
        "produto": "uq_wms_produto_id_empresa",
        "lote": "uq_wms_lote_id_empresa",
        "recebimento": "uq_wms_recebimento_id_empresa",
        "recebimento_item": "uq_wms_recebimento_item_id_empresa",
        "alocacao": "uq_wms_alocacao_id_empresa",
        "estoque": "uq_wms_estoque_id_empresa",
        "movimentacao_estoque": "uq_wms_movimentacao_id_empresa",
    }

    for tabela, constraint in constraints_unicas.items():
        op.execute(
            f"""
            ALTER TABLE wms.{tabela}
            ADD CONSTRAINT {constraint}
            UNIQUE (id, empresa_id)
            """
        )

    # Códigos e SKU únicos dentro da empresa.
    op.execute("""
        ALTER TABLE wms.centro_distribuicao
        ADD CONSTRAINT uq_wms_cd_empresa_codigo
        UNIQUE (empresa_id, codigo);

        ALTER TABLE wms.produto
        ADD CONSTRAINT uq_wms_produto_empresa_sku
        UNIQUE (empresa_id, sku);

        ALTER TABLE wms.carga
        ADD CONSTRAINT uq_wms_carga_empresa_codigo
        UNIQUE (empresa_id, codigo);

        ALTER TABLE wms.recebimento
        ADD CONSTRAINT uq_wms_recebimento_empresa_codigo
        UNIQUE (empresa_id, codigo);
    """)

    # Identificador externo pode ser nulo, mas não se repete na mesma empresa.
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS
        uq_wms_carga_empresa_coleta_externa
        ON wms.carga (empresa_id, coleta_externa_id)
        WHERE coleta_externa_id IS NOT NULL;
    """)

    # Lote precisa pertencer ao mesmo produto e à mesma empresa.
    op.execute("""
        ALTER TABLE wms.lote
        ADD CONSTRAINT uq_wms_lote_id_produto_empresa
        UNIQUE (id, produto_id, empresa_id);
    """)

    # Relações entre centros de distribuição, zonas e endereços.
    op.execute("""
        ALTER TABLE wms.zona
        ADD CONSTRAINT fk_wms_zona_cd_empresa
        FOREIGN KEY (cd_id, empresa_id)
        REFERENCES wms.centro_distribuicao(id, empresa_id);

        ALTER TABLE wms.endereco
        ADD CONSTRAINT fk_wms_endereco_cd_empresa
        FOREIGN KEY (cd_id, empresa_id)
        REFERENCES wms.centro_distribuicao(id, empresa_id);
    """)

    # Carga pertence a um CD da mesma empresa.
    op.execute("""
        ALTER TABLE wms.carga
        ADD CONSTRAINT fk_wms_carga_cd_empresa
        FOREIGN KEY (cd_id, empresa_id)
        REFERENCES wms.centro_distribuicao(id, empresa_id);
    """)

    # Produto e lote.
    op.execute("""
        ALTER TABLE wms.lote
        ADD CONSTRAINT fk_wms_lote_produto_empresa
        FOREIGN KEY (produto_id, empresa_id)
        REFERENCES wms.produto(id, empresa_id);
    """)

    # Recebimento e carga.
    op.execute("""
        ALTER TABLE wms.recebimento
        ADD CONSTRAINT fk_wms_recebimento_carga_empresa
        FOREIGN KEY (carga_id, empresa_id)
        REFERENCES wms.carga(id, empresa_id);
    """)

    # Itens: recebimento, produto e lote precisam pertencer à mesma empresa.
    op.execute("""
        ALTER TABLE wms.recebimento_item
        ADD CONSTRAINT fk_wms_item_recebimento_empresa
        FOREIGN KEY (recebimento_id, empresa_id)
        REFERENCES wms.recebimento(id, empresa_id)
        ON DELETE CASCADE;

        ALTER TABLE wms.recebimento_item
        ADD CONSTRAINT fk_wms_item_produto_empresa
        FOREIGN KEY (produto_id, empresa_id)
        REFERENCES wms.produto(id, empresa_id);

        ALTER TABLE wms.recebimento_item
        ADD CONSTRAINT fk_wms_item_lote_produto_empresa
        FOREIGN KEY (lote_id, produto_id, empresa_id)
        REFERENCES wms.lote(id, produto_id, empresa_id);
    """)

    # Alocação: item recebido e endereço devem ser da mesma empresa.
    op.execute("""
        ALTER TABLE wms.alocacao
        ADD CONSTRAINT fk_wms_alocacao_item_empresa
        FOREIGN KEY (recebimento_item_id, empresa_id)
        REFERENCES wms.recebimento_item(id, empresa_id);

        ALTER TABLE wms.alocacao
        ADD CONSTRAINT fk_wms_alocacao_endereco_empresa
        FOREIGN KEY (endereco_id, empresa_id)
        REFERENCES wms.endereco(id, empresa_id);
    """)

    # Estoque: endereço, produto e lote devem pertencer à mesma empresa.
    op.execute("""
        ALTER TABLE wms.estoque
        ADD CONSTRAINT fk_wms_estoque_endereco_empresa
        FOREIGN KEY (endereco_id, empresa_id)
        REFERENCES wms.endereco(id, empresa_id);

        ALTER TABLE wms.estoque
        ADD CONSTRAINT fk_wms_estoque_produto_empresa
        FOREIGN KEY (produto_id, empresa_id)
        REFERENCES wms.produto(id, empresa_id);

        ALTER TABLE wms.estoque
        ADD CONSTRAINT fk_wms_estoque_lote_produto_empresa
        FOREIGN KEY (lote_id, produto_id, empresa_id)
        REFERENCES wms.lote(id, produto_id, empresa_id);
    """)

    # Histórico de movimentações também respeita o isolamento.
    op.execute("""
        ALTER TABLE wms.movimentacao_estoque
        ADD CONSTRAINT fk_wms_mov_endereco_empresa
        FOREIGN KEY (endereco_id, empresa_id)
        REFERENCES wms.endereco(id, empresa_id);

        ALTER TABLE wms.movimentacao_estoque
        ADD CONSTRAINT fk_wms_mov_produto_empresa
        FOREIGN KEY (produto_id, empresa_id)
        REFERENCES wms.produto(id, empresa_id);

        ALTER TABLE wms.movimentacao_estoque
        ADD CONSTRAINT fk_wms_mov_lote_produto_empresa
        FOREIGN KEY (lote_id, produto_id, empresa_id)
        REFERENCES wms.lote(id, produto_id, empresa_id);
    """)

def downgrade() -> None:
    """Impede a remoção acidental da estrutura operacional e dos dados."""

    raise RuntimeError(
        "Downgrade bloqueado: a remoção da estrutura operacional WMS "
        "deve ser planejada e executada separadamente."
    )
