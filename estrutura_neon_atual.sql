--
-- PostgreSQL database dump
--

\restrict 0fWQkN81WfL5tHYf81MHFVuSnbXEj8offWR4eD2HPhInje73VhMcVS9aUsPKeV2

-- Dumped from database version 18.7 (3190d2f)
-- Dumped by pg_dump version 18.7 (Ubuntu 18.7-1.pgdg24.04+5)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: wms; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA wms;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alocacao; Type: TABLE; Schema: wms; Owner: -
--

CREATE TABLE wms.alocacao (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    recebimento_item_id uuid NOT NULL,
    endereco_id uuid NOT NULL,
    quantidade integer NOT NULL,
    alocado_por text,
    alocado_em timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT alocacao_quantidade_check CHECK ((quantidade > 0))
);


--
-- Name: carga; Type: TABLE; Schema: wms; Owner: -
--

CREATE TABLE wms.carga (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    codigo text NOT NULL,
    cd_id uuid NOT NULL,
    coleta_externa_id text,
    origem text,
    status text DEFAULT 'PREVISTA'::text NOT NULL,
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT carga_status_check CHECK ((status = ANY (ARRAY['PREVISTA'::text, 'CHEGOU'::text, 'DESCARREGADA'::text])))
);


--
-- Name: centro_distribuicao; Type: TABLE; Schema: wms; Owner: -
--

CREATE TABLE wms.centro_distribuicao (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    codigo text NOT NULL,
    nome text NOT NULL,
    cidade text,
    uf character(2),
    ativo boolean DEFAULT true NOT NULL,
    criado_em timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: endereco; Type: TABLE; Schema: wms; Owner: -
--

CREATE TABLE wms.endereco (
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
    CONSTRAINT endereco_capacidade_check CHECK ((capacidade > 0))
);


--
-- Name: estoque; Type: TABLE; Schema: wms; Owner: -
--

CREATE TABLE wms.estoque (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    endereco_id uuid NOT NULL,
    produto_id uuid NOT NULL,
    lote_id uuid,
    quantidade integer DEFAULT 0 NOT NULL,
    quantidade_reservada integer DEFAULT 0 NOT NULL,
    atualizado_em timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_reserva_menor_saldo CHECK ((quantidade_reservada <= quantidade)),
    CONSTRAINT estoque_quantidade_check CHECK ((quantidade >= 0)),
    CONSTRAINT estoque_quantidade_reservada_check CHECK ((quantidade_reservada >= 0))
);


--
-- Name: lote; Type: TABLE; Schema: wms; Owner: -
--

CREATE TABLE wms.lote (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    produto_id uuid NOT NULL,
    codigo text NOT NULL,
    validade date,
    criado_em timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: movimentacao_estoque; Type: TABLE; Schema: wms; Owner: -
--

CREATE TABLE wms.movimentacao_estoque (
    id bigint NOT NULL,
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
    CONSTRAINT ck_tipo_sinal CHECK ((((tipo = 'ENTRADA'::text) AND (delta > 0)) OR ((tipo = 'SAIDA'::text) AND (delta < 0)) OR (tipo = 'AJUSTE'::text))),
    CONSTRAINT movimentacao_estoque_delta_check CHECK ((delta <> 0)),
    CONSTRAINT movimentacao_estoque_ref_tipo_check CHECK ((ref_tipo = ANY (ARRAY['ALOCACAO'::text, 'PICKING'::text, 'EXPEDICAO'::text, 'INVENTARIO'::text, 'AJUSTE_MANUAL'::text]))),
    CONSTRAINT movimentacao_estoque_saldo_apos_check CHECK ((saldo_apos >= 0)),
    CONSTRAINT movimentacao_estoque_tipo_check CHECK ((tipo = ANY (ARRAY['ENTRADA'::text, 'SAIDA'::text, 'AJUSTE'::text])))
);


--
-- Name: movimentacao_estoque_id_seq; Type: SEQUENCE; Schema: wms; Owner: -
--

ALTER TABLE wms.movimentacao_estoque ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME wms.movimentacao_estoque_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: produto; Type: TABLE; Schema: wms; Owner: -
--

CREATE TABLE wms.produto (
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
    CONSTRAINT produto_check CHECK (((estoque_maximo IS NULL) OR (estoque_maximo >= estoque_minimo))),
    CONSTRAINT produto_estoque_minimo_check CHECK ((estoque_minimo >= 0)),
    CONSTRAINT produto_peso_kg_check CHECK ((peso_kg >= (0)::numeric)),
    CONSTRAINT produto_volume_m3_check CHECK ((volume_m3 >= (0)::numeric))
);


--
-- Name: seq_recebimento; Type: SEQUENCE; Schema: wms; Owner: -
--

CREATE SEQUENCE wms.seq_recebimento
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: recebimento; Type: TABLE; Schema: wms; Owner: -
--

CREATE TABLE wms.recebimento (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    codigo text DEFAULT ('REC-'::text || lpad((nextval('wms.seq_recebimento'::regclass))::text, 6, '0'::text)) NOT NULL,
    carga_id uuid NOT NULL,
    nota_fiscal text,
    status text DEFAULT 'AGUARDANDO'::text NOT NULL,
    conferido_em timestamp with time zone,
    conferido_por text,
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT recebimento_status_check CHECK ((status = ANY (ARRAY['AGUARDANDO'::text, 'EM_CONFERENCIA'::text, 'CONFERIDA'::text, 'COM_DIVERGENCIA'::text, 'ARMAZENADA'::text])))
);


--
-- Name: recebimento_item; Type: TABLE; Schema: wms; Owner: -
--

CREATE TABLE wms.recebimento_item (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    recebimento_id uuid NOT NULL,
    produto_id uuid NOT NULL,
    lote_id uuid,
    qtd_esperada integer NOT NULL,
    qtd_conferida integer,
    divergencia boolean GENERATED ALWAYS AS (((qtd_conferida IS NOT NULL) AND (qtd_conferida <> qtd_esperada))) STORED,
    CONSTRAINT recebimento_item_qtd_conferida_check CHECK ((qtd_conferida >= 0)),
    CONSTRAINT recebimento_item_qtd_esperada_check CHECK ((qtd_esperada > 0))
);


--
-- Name: seq_embalagem; Type: SEQUENCE; Schema: wms; Owner: -
--

CREATE SEQUENCE wms.seq_embalagem
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: seq_expedicao; Type: SEQUENCE; Schema: wms; Owner: -
--

CREATE SEQUENCE wms.seq_expedicao
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: seq_picking; Type: SEQUENCE; Schema: wms; Owner: -
--

CREATE SEQUENCE wms.seq_picking
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: zona; Type: TABLE; Schema: wms; Owner: -
--

CREATE TABLE wms.zona (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    cd_id uuid NOT NULL,
    codigo text NOT NULL,
    nome text NOT NULL,
    tipo text NOT NULL,
    CONSTRAINT zona_tipo_check CHECK ((tipo = ANY (ARRAY['RECEBIMENTO'::text, 'ARMAZENAGEM'::text, 'PICKING'::text, 'PACKING'::text, 'EXPEDICAO'::text, 'QUARENTENA'::text])))
);


--
-- Name: alocacao alocacao_pkey; Type: CONSTRAINT; Schema: wms; Owner: -
--

ALTER TABLE ONLY wms.alocacao
    ADD CONSTRAINT alocacao_pkey PRIMARY KEY (id);


--
-- Name: carga carga_codigo_key; Type: CONSTRAINT; Schema: wms; Owner: -
--

ALTER TABLE ONLY wms.carga
    ADD CONSTRAINT carga_codigo_key UNIQUE (codigo);


--
-- Name: carga carga_coleta_externa_id_key; Type: CONSTRAINT; Schema: wms; Owner: -
--

ALTER TABLE ONLY wms.carga
    ADD CONSTRAINT carga_coleta_externa_id_key UNIQUE (coleta_externa_id);


--
-- Name: carga carga_pkey; Type: CONSTRAINT; Schema: wms; Owner: -
--

ALTER TABLE ONLY wms.carga
    ADD CONSTRAINT carga_pkey PRIMARY KEY (id);


--
-- Name: centro_distribuicao centro_distribuicao_codigo_key; Type: CONSTRAINT; Schema: wms; Owner: -
--

ALTER TABLE ONLY wms.centro_distribuicao
    ADD CONSTRAINT centro_distribuicao_codigo_key UNIQUE (codigo);


--
-- Name: centro_distribuicao centro_distribuicao_pkey; Type: CONSTRAINT; Schema: wms; Owner: -
--

ALTER TABLE ONLY wms.centro_distribuicao
    ADD CONSTRAINT centro_distribuicao_pkey PRIMARY KEY (id);


--
-- Name: endereco endereco_cd_id_codigo_key; Type: CONSTRAINT; Schema: wms; Owner: -
--

ALTER TABLE ONLY wms.endereco
    ADD CONSTRAINT endereco_cd_id_codigo_key UNIQUE (cd_id, codigo);


--
-- Name: endereco endereco_pkey; Type: CONSTRAINT; Schema: wms; Owner: -
--

ALTER TABLE ONLY wms.endereco
    ADD CONSTRAINT endereco_pkey PRIMARY KEY (id);


--
-- Name: estoque estoque_endereco_id_produto_id_lote_id_key; Type: CONSTRAINT; Schema: wms; Owner: -
--

ALTER TABLE ONLY wms.estoque
    ADD CONSTRAINT estoque_endereco_id_produto_id_lote_id_key UNIQUE NULLS NOT DISTINCT (endereco_id, produto_id, lote_id);


--
-- Name: estoque estoque_pkey; Type: CONSTRAINT; Schema: wms; Owner: -
--

ALTER TABLE ONLY wms.estoque
    ADD CONSTRAINT estoque_pkey PRIMARY KEY (id);


--
-- Name: lote lote_pkey; Type: CONSTRAINT; Schema: wms; Owner: -
--

ALTER TABLE ONLY wms.lote
    ADD CONSTRAINT lote_pkey PRIMARY KEY (id);


--
-- Name: lote lote_produto_id_codigo_key; Type: CONSTRAINT; Schema: wms; Owner: -
--

ALTER TABLE ONLY wms.lote
    ADD CONSTRAINT lote_produto_id_codigo_key UNIQUE (produto_id, codigo);


--
-- Name: movimentacao_estoque movimentacao_estoque_pkey; Type: CONSTRAINT; Schema: wms; Owner: -
--

ALTER TABLE ONLY wms.movimentacao_estoque
    ADD CONSTRAINT movimentacao_estoque_pkey PRIMARY KEY (id);


--
-- Name: produto produto_pkey; Type: CONSTRAINT; Schema: wms; Owner: -
--

ALTER TABLE ONLY wms.produto
    ADD CONSTRAINT produto_pkey PRIMARY KEY (id);


--
-- Name: produto produto_sku_key; Type: CONSTRAINT; Schema: wms; Owner: -
--

ALTER TABLE ONLY wms.produto
    ADD CONSTRAINT produto_sku_key UNIQUE (sku);


--
-- Name: recebimento recebimento_carga_id_nota_fiscal_key; Type: CONSTRAINT; Schema: wms; Owner: -
--

ALTER TABLE ONLY wms.recebimento
    ADD CONSTRAINT recebimento_carga_id_nota_fiscal_key UNIQUE (carga_id, nota_fiscal);


--
-- Name: recebimento recebimento_codigo_key; Type: CONSTRAINT; Schema: wms; Owner: -
--

ALTER TABLE ONLY wms.recebimento
    ADD CONSTRAINT recebimento_codigo_key UNIQUE (codigo);


--
-- Name: recebimento_item recebimento_item_pkey; Type: CONSTRAINT; Schema: wms; Owner: -
--

ALTER TABLE ONLY wms.recebimento_item
    ADD CONSTRAINT recebimento_item_pkey PRIMARY KEY (id);


--
-- Name: recebimento_item recebimento_item_recebimento_id_produto_id_lote_id_key; Type: CONSTRAINT; Schema: wms; Owner: -
--

ALTER TABLE ONLY wms.recebimento_item
    ADD CONSTRAINT recebimento_item_recebimento_id_produto_id_lote_id_key UNIQUE NULLS NOT DISTINCT (recebimento_id, produto_id, lote_id);


--
-- Name: recebimento recebimento_pkey; Type: CONSTRAINT; Schema: wms; Owner: -
--

ALTER TABLE ONLY wms.recebimento
    ADD CONSTRAINT recebimento_pkey PRIMARY KEY (id);


--
-- Name: zona zona_cd_id_codigo_key; Type: CONSTRAINT; Schema: wms; Owner: -
--

ALTER TABLE ONLY wms.zona
    ADD CONSTRAINT zona_cd_id_codigo_key UNIQUE (cd_id, codigo);


--
-- Name: zona zona_id_cd_id_key; Type: CONSTRAINT; Schema: wms; Owner: -
--

ALTER TABLE ONLY wms.zona
    ADD CONSTRAINT zona_id_cd_id_key UNIQUE (id, cd_id);


--
-- Name: zona zona_pkey; Type: CONSTRAINT; Schema: wms; Owner: -
--

ALTER TABLE ONLY wms.zona
    ADD CONSTRAINT zona_pkey PRIMARY KEY (id);


--
-- Name: ix_alocacao_item; Type: INDEX; Schema: wms; Owner: -
--

CREATE INDEX ix_alocacao_item ON wms.alocacao USING btree (recebimento_item_id);


--
-- Name: ix_endereco_zona; Type: INDEX; Schema: wms; Owner: -
--

CREATE INDEX ix_endereco_zona ON wms.endereco USING btree (zona_id);


--
-- Name: ix_estoque_produto; Type: INDEX; Schema: wms; Owner: -
--

CREATE INDEX ix_estoque_produto ON wms.estoque USING btree (produto_id);


--
-- Name: ix_mov_endereco; Type: INDEX; Schema: wms; Owner: -
--

CREATE INDEX ix_mov_endereco ON wms.movimentacao_estoque USING btree (endereco_id);


--
-- Name: ix_mov_produto_data; Type: INDEX; Schema: wms; Owner: -
--

CREATE INDEX ix_mov_produto_data ON wms.movimentacao_estoque USING btree (produto_id, criado_em DESC);


--
-- Name: ix_recebimento_status; Type: INDEX; Schema: wms; Owner: -
--

CREATE INDEX ix_recebimento_status ON wms.recebimento USING btree (status);


--
-- Name: alocacao alocacao_endereco_id_fkey; Type: FK CONSTRAINT; Schema: wms; Owner: -
--

ALTER TABLE ONLY wms.alocacao
    ADD CONSTRAINT alocacao_endereco_id_fkey FOREIGN KEY (endereco_id) REFERENCES wms.endereco(id);


--
-- Name: alocacao alocacao_recebimento_item_id_fkey; Type: FK CONSTRAINT; Schema: wms; Owner: -
--

ALTER TABLE ONLY wms.alocacao
    ADD CONSTRAINT alocacao_recebimento_item_id_fkey FOREIGN KEY (recebimento_item_id) REFERENCES wms.recebimento_item(id);


--
-- Name: carga carga_cd_id_fkey; Type: FK CONSTRAINT; Schema: wms; Owner: -
--

ALTER TABLE ONLY wms.carga
    ADD CONSTRAINT carga_cd_id_fkey FOREIGN KEY (cd_id) REFERENCES wms.centro_distribuicao(id);


--
-- Name: endereco endereco_zona_id_cd_id_fkey; Type: FK CONSTRAINT; Schema: wms; Owner: -
--

ALTER TABLE ONLY wms.endereco
    ADD CONSTRAINT endereco_zona_id_cd_id_fkey FOREIGN KEY (zona_id, cd_id) REFERENCES wms.zona(id, cd_id);


--
-- Name: estoque estoque_endereco_id_fkey; Type: FK CONSTRAINT; Schema: wms; Owner: -
--

ALTER TABLE ONLY wms.estoque
    ADD CONSTRAINT estoque_endereco_id_fkey FOREIGN KEY (endereco_id) REFERENCES wms.endereco(id);


--
-- Name: estoque estoque_lote_id_fkey; Type: FK CONSTRAINT; Schema: wms; Owner: -
--

ALTER TABLE ONLY wms.estoque
    ADD CONSTRAINT estoque_lote_id_fkey FOREIGN KEY (lote_id) REFERENCES wms.lote(id);


--
-- Name: estoque estoque_produto_id_fkey; Type: FK CONSTRAINT; Schema: wms; Owner: -
--

ALTER TABLE ONLY wms.estoque
    ADD CONSTRAINT estoque_produto_id_fkey FOREIGN KEY (produto_id) REFERENCES wms.produto(id);


--
-- Name: lote lote_produto_id_fkey; Type: FK CONSTRAINT; Schema: wms; Owner: -
--

ALTER TABLE ONLY wms.lote
    ADD CONSTRAINT lote_produto_id_fkey FOREIGN KEY (produto_id) REFERENCES wms.produto(id);


--
-- Name: movimentacao_estoque movimentacao_estoque_endereco_id_fkey; Type: FK CONSTRAINT; Schema: wms; Owner: -
--

ALTER TABLE ONLY wms.movimentacao_estoque
    ADD CONSTRAINT movimentacao_estoque_endereco_id_fkey FOREIGN KEY (endereco_id) REFERENCES wms.endereco(id);


--
-- Name: movimentacao_estoque movimentacao_estoque_lote_id_fkey; Type: FK CONSTRAINT; Schema: wms; Owner: -
--

ALTER TABLE ONLY wms.movimentacao_estoque
    ADD CONSTRAINT movimentacao_estoque_lote_id_fkey FOREIGN KEY (lote_id) REFERENCES wms.lote(id);


--
-- Name: movimentacao_estoque movimentacao_estoque_produto_id_fkey; Type: FK CONSTRAINT; Schema: wms; Owner: -
--

ALTER TABLE ONLY wms.movimentacao_estoque
    ADD CONSTRAINT movimentacao_estoque_produto_id_fkey FOREIGN KEY (produto_id) REFERENCES wms.produto(id);


--
-- Name: recebimento recebimento_carga_id_fkey; Type: FK CONSTRAINT; Schema: wms; Owner: -
--

ALTER TABLE ONLY wms.recebimento
    ADD CONSTRAINT recebimento_carga_id_fkey FOREIGN KEY (carga_id) REFERENCES wms.carga(id);


--
-- Name: recebimento_item recebimento_item_lote_id_fkey; Type: FK CONSTRAINT; Schema: wms; Owner: -
--

ALTER TABLE ONLY wms.recebimento_item
    ADD CONSTRAINT recebimento_item_lote_id_fkey FOREIGN KEY (lote_id) REFERENCES wms.lote(id);


--
-- Name: recebimento_item recebimento_item_produto_id_fkey; Type: FK CONSTRAINT; Schema: wms; Owner: -
--

ALTER TABLE ONLY wms.recebimento_item
    ADD CONSTRAINT recebimento_item_produto_id_fkey FOREIGN KEY (produto_id) REFERENCES wms.produto(id);


--
-- Name: recebimento_item recebimento_item_recebimento_id_fkey; Type: FK CONSTRAINT; Schema: wms; Owner: -
--

ALTER TABLE ONLY wms.recebimento_item
    ADD CONSTRAINT recebimento_item_recebimento_id_fkey FOREIGN KEY (recebimento_id) REFERENCES wms.recebimento(id) ON DELETE CASCADE;


--
-- Name: zona zona_cd_id_fkey; Type: FK CONSTRAINT; Schema: wms; Owner: -
--

ALTER TABLE ONLY wms.zona
    ADD CONSTRAINT zona_cd_id_fkey FOREIGN KEY (cd_id) REFERENCES wms.centro_distribuicao(id);


--
-- PostgreSQL database dump complete
--

\unrestrict 0fWQkN81WfL5tHYf81MHFVuSnbXEj8offWR4eD2HPhInje73VhMcVS9aUsPKeV2

