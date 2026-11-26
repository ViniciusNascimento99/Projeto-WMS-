# SIG-Log WMS — Gestão de Estoque e Centro de Distribuição

> **Squad 01** · Plataforma **SIG-Log** (Sistema de Informações Gerenciais de Logística Multimodal)
> Disciplina: Análise de Sistemas II

## Sumário

1. [Sobre o projeto](#1-sobre-o-projeto)
2. [Problema e objetivo](#2-problema-e-objetivo)
3. [Escopo funcional](#3-escopo-funcional)
4. [Arquitetura (alvo)](#4-arquitetura-alvo)
5. [Contrato da API](#5-contrato-da-api)
6. [Eventos e mensageria](#6-eventos-e-mensageria)
7. [Tecnologias](#7-tecnologias)
8. [Estrutura do repositório](#8-estrutura-do-repositório)
9. [Como executar](#9-como-executar)
10. [Testes](#10-testes)
11. [Status do projeto](#11-status-do-projeto)
12. [Equipe](#12-equipe)

## 1. Sobre o projeto

O **SIG-Log WMS** é o módulo responsável por gerenciar o fluxo físico de mercadorias dentro dos Centros de Distribuição (CDs) de uma grande empresa logística nacional.

Ele é um dos seis módulos da plataforma SIG-Log, que se integram por **APIs REST** e **mensageria (RabbitMQ)**:

| Módulo                                  | Responsabilidade                                       |
| --------------------------------------- | ------------------------------------------------------ |
| **WMS & Estoque/CD** (este repositório) | Recebimento, armazenagem, picking, packing e expedição |
| Frota/Modais & Roteirização             | Veículos, modais e rotas                               |
| Rastreamento de Cargas & Telemetria IoT | Tracking e sensores                                    |
| Financeiro & Faturamento                | Cobrança e faturamento                                 |
| RH/Jornada & Escalonamento              | Jornada e escalas                                      |
| CRM/SAC & Portal do Cliente             | Atendimento e portal do cliente                        |

Cada Squad é dona do seu domínio (*bounded context*): os módulos se integram respeitando os contratos de API e o catálogo de eventos publicados.

## 2. Problema e objetivo

**Problema:** gerenciar o fluxo físico de mercadorias dentro dos CDs, do recebimento à expedição.

**Objetivo:** controlar uma carga desde a sua entrada no CD até a sua saída:

```
Recebimento → Conferência → Endereçamento → Armazenagem → Picking → Packing → Expedição
```

## 3. Escopo funcional

**Entidades do domínio:** `Produto` · `Carga` · `Pedido` · `Estoque` · `Localizacao` · `Endereco` · `PickingOrder` · `PackingOrder` · `Expedicao` · `MovimentacaoEstoque`

### Casos de uso

| Código | Caso de uso                     |
| ------ | ------------------------------- |
| UC01   | Receber mercadoria              |
| UC02   | Conferir mercadoria             |
| UC03   | Criar endereço de armazenamento |
| UC04   | Alocar produto                  |
| UC05   | Consultar estoque               |
| UC06   | Gerar ordem de picking          |
| UC07   | Registrar separação             |
| UC08   | Embalar pedido                  |
| UC09   | Expedir carga                   |
| UC10   | Atualizar saldo de estoque      |

### Requisitos funcionais

| Código | Descrição                  |
| ------ | -------------------------- |
| RF01   | Cadastro de produtos       |
| RF02   | Cadastro de posições       |
| RF03   | Registro de recebimento    |
| RF04   | Atualização do estoque     |
| RF05   | Endereçamento              |
| RF06   | Picking                    |
| RF07   | Packing                    |
| RF08   | Expedição                  |
| RF09   | Consulta de estoque        |
| RF10   | Histórico de movimentações |

## 4. Arquitetura (alvo)

O serviço será organizado em camadas, seguindo DDD:

```
┌──────────────────────────────────┐
│ API LAYER                        │  REST / OpenAPI / Controllers
├──────────────────────────────────┤
│ APPLICATION LAYER                │  Use Cases / Services / DTOs
├──────────────────────────────────┤
│ DOMAIN                           │  Entities / Rules / Events
├──────────────────────────────────┤
│ INFRASTRUCTURE                   │  DB / RabbitMQ / External APIs
├──────────────────────────────────┤
│ OBSERVABILITY                    │  Logs / Metrics / Tracing
└──────────────────────────────────┘
```

- **Persistência:** PostgreSQL, no padrão *Database-per-Service* (banco do WMS isolado dos demais módulos).
- **Integração síncrona:** REST, conforme o contrato [`openapi.yaml`](openapi.yaml).
- **Integração assíncrona:** eventos via RabbitMQ, conforme [`events.schema.json`](events.schema.json) e [`rabbitmq-definitions.json`](rabbitmq-definitions.json).

> As pastas de `src/` e `tests/` já foram criadas, mas ainda sem código. Hoje o repositório contém principalmente os **contratos** de API e de eventos.

## 5. Contrato da API

Definido em [`openapi.yaml`](openapi.yaml) (OpenAPI 3.0.3, versão 1.0.0).

- **Base URL (desenvolvimento):** `http://localhost:8001/api/v1`
- **Autenticação:** Bearer JWT

| Método | Endpoint                            | Descrição                           | Caso de uso / RF |
| ------ | ----------------------------------- | ----------------------------------- | ---------------- |
| POST   | `/products`                         | Cadastrar produto                   | RF01             |
| GET    | `/products/{id}`                    | Consultar produto                   | —                |
| POST   | `/addresses`                        | Criar endereço de armazenamento     | UC03, RF02       |
| POST   | `/receipts`                         | Registrar recebimento de mercadoria | UC01, RF03       |
| POST   | `/receipts/{id}/conference`         | Conferir mercadoria recebida        | UC02             |
| POST   | `/allocations`                      | Alocar produto em um endereço       | UC04, RF05       |
| GET    | `/inventory`                        | Consultar estoque                   | UC05, RF09       |
| GET    | `/inventory/{product_id}`           | Saldo de um produto por endereço    | —                |
| GET    | `/inventory/{product_id}/movements` | Histórico de movimentações          | RF10             |
| POST   | `/picking`                          | Gerar ordem de picking              | UC06, RF06       |
| POST   | `/picking/{id}/pick`                | Registrar separação de itens        | UC07             |
| POST   | `/packing`                          | Embalar pedido separado             | UC08, RF07       |
| POST   | `/shipments`                        | Expedir carga                       | UC09, RF08       |
| GET    | `/shipments/{id}`                   | Consultar expedição                 | —                |

`GET /inventory` aceita os parâmetros `address`, `page` (padrão 1) e `size` (padrão 20).

### Estados dos recursos

| Recurso            | Valores possíveis                                                    |
| ------------------ | -------------------------------------------------------------------- |
| Recebimento        | `AGUARDANDO`, `EM_CONFERENCIA`, `CONFERIDA`, `COM_DIVERGENCIA`, `ARMAZENADA` |
| Ordem de picking   | `CRIADA`, `EM_SEPARACAO`, `SEPARADA`, `CANCELADA`                    |
| Ordem de packing   | `CRIADA`, `EM_EMBALAGEM`, `EMBALADA`                                 |
| Expedição          | `PLANEJADA`, `EXPEDIDA`                                              |
| Movimentação       | `ENTRADA`, `SAIDA`, `AJUSTE`                                         |

### Erros

As respostas de erro seguem o formato `{ "code": "...", "message": "..." }`:

| Status | Significado                       | Exemplo                                              |
| ------ | --------------------------------- | ---------------------------------------------------- |
| 400    | Requisição inválida               | Campo obrigatório ausente                            |
| 404    | Recurso não encontrado            | Produto ou recebimento inexistente                   |
| 409    | Conflito com o estado atual       | Saldo insuficiente ao gerar picking (`INSUFFICIENT_STOCK`) |

### Exemplos de requisição

Exemplos baseados no contrato. A API ainda não está implementada; use-os como referência de payload.

```bash
# Cadastrar produto (RF01)
curl -X POST http://localhost:8001/api/v1/products \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"sku": "SKU-0001", "description": "Caixa de parafusos 100un", "unit": "CX"}'

# Criar endereço de armazenamento (UC03)
curl -X POST http://localhost:8001/api/v1/addresses \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"code": "A-01-03-2", "aisle": "A", "shelf": "01", "level": 2, "capacity": 500}'

# Registrar recebimento (UC01)
curl -X POST http://localhost:8001/api/v1/receipts \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"cargoId": "CARGA-001", "invoiceNumber": "NF-12345", "items": [{"productId": "SKU-0001", "expectedQuantity": 100}]}'

# Gerar ordem de picking (UC06)
curl -X POST http://localhost:8001/api/v1/picking \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"orderId": "PED-100", "items": [{"productId": "SKU-0001", "quantity": 10}]}'

# Expedir carga (UC09)
curl -X POST http://localhost:8001/api/v1/shipments \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"orderIds": ["PED-100"], "destination": "Recife - PE"}'
```

## 6. Eventos e mensageria

### Eventos publicados pelo WMS

Todos os eventos seguem o schema [`events.schema.json`](events.schema.json) (JSON Schema 2020-12) e carregam os campos comuns `event`, `version`, `eventId`, `timestamp`, `correlationId` e `source`. Exemplos válidos estão em [`events.examples.json`](events.examples.json).

| Evento               | Routing key                  | Quando ocorre                            | Campos específicos                                         |
| -------------------- | ---------------------------- | ---------------------------------------- | ---------------------------------------------------------- |
| `MercadoriaRecebida` | `wms.mercadoria.recebida.v1` | Conferência concluída sem divergência    | `cargoId`, `receiptId`, `invoiceNumber` (opcional), `items[]` |
| `ProdutoArmazenado`  | `wms.produto.armazenado.v1`  | Produto é alocado em um endereço         | `productId`, `addressCode`, `quantity`                     |
| `EstoqueAtualizado`  | `wms.estoque.atualizado.v1`  | Saldo de estoque é alterado              | `productId`, `addressCode`, `delta`, `balance`, `reason`   |
| `PickingCriado`      | `wms.picking.criado.v1`      | Ordem de picking é gerada                | `pickingId`, `orderId`                                     |
| `PedidoSeparado`     | `wms.pedido.separado.v1`     | Todos os itens do pedido foram separados | `pickingId`, `orderId`                                     |
| `PedidoEmbalado`     | `wms.pedido.embalado.v1`     | Embalagem concluída                      | `packingId`, `orderId`, `volumes`                          |
| `CargaExpedida`      | `wms.carga.expedida.v1`      | Carga sai do CD                          | `shipmentId`, `orderIds[]`, `destination`                  |

Exemplo (`CargaExpedida`):

```json
{
  "event": "CargaExpedida",
  "version": 1,
  "eventId": "7d1f9b3e-2c64-4a1d-9f10-5b0c3a8e4d21",
  "timestamp": "2026-10-12T14:30:00Z",
  "correlationId": "PED-100",
  "source": "wms",
  "shipmentId": "EXP-001",
  "orderIds": ["PED-100"],
  "destination": "Recife - PE"
}
```

### Topologia do RabbitMQ

Definida em [`rabbitmq-definitions.json`](rabbitmq-definitions.json) (RabbitMQ 3.13, filas do tipo *quorum*, com *dead-letter queue* para cada fila).

**Exchange de saída:** `siglog.wms.events` (topic). Filas dos consumidores:

| Fila                    | Módulo     | Eventos recebidos                                            |
| ----------------------- | ---------- | ------------------------------------------------------------ |
| `tracking.wms.events`   | Tracking   | MercadoriaRecebida, ProdutoArmazenado, CargaExpedida         |
| `financeiro.wms.events` | Financeiro | MercadoriaRecebida, EstoqueAtualizado, CargaExpedida         |
| `crm.wms.events`        | CRM        | PickingCriado, PedidoSeparado, PedidoEmbalado, CargaExpedida |
| `frota.wms.events`      | Frota      | PedidoEmbalado, CargaExpedida                                |

**Mensagens que o WMS consome:**

| Fila                | Origem                | Mensagem                   |
| ------------------- | --------------------- | -------------------------- |
| `wms.pedidos.inbox` | `siglog.crm.events`   | `crm.pedido.criado.v1`     |
| `wms.coletas.inbox` | `siglog.frota.events` | `frota.coleta.agendada.v1` |

Mensagens rejeitadas vão para o exchange `siglog.wms.dlx` (direct), que as encaminha para as filas `*.dlq`.

## 7. Tecnologias

| Área                  | Tecnologia                                 | Situação                                    |
| --------------------- | ------------------------------------------ | ------------------------------------------- |
| Linguagem / API       | Python, FastAPI                            | Dependências listadas em `requirements.txt` |
| Contratos             | OpenAPI 3.0.3, JSON Schema 2020-12         | Em uso                                      |
| Mensageria            | RabbitMQ                                   | Topologia definida                          |
| Banco de dados        | PostgreSQL                                 | Planejado                                   |
| Contêineres           | Docker e Docker Compose                    | Planejado                                   |
| CI/CD                 | GitHub Actions                             | Planejado                                   |
| Observabilidade       | OpenTelemetry, Prometheus, Grafana, Jaeger | Planejado                                   |
| Qualidade e segurança | SonarQube, Trivy                           | Planejado                                   |
| Teste de carga        | K6                                         | Planejado                                   |

## 8. Estrutura do repositório

**Hoje:**

```
Projeto-WMS-/
├── README.md
├── .gitignore
├── requirements.txt
├── openapi.yaml                # contrato da API
├── events.schema.json          # schema dos eventos
├── events.examples.json        # exemplos de eventos
├── rabbitmq-definitions.json   # exchanges, filas e bindings
├── testar_eventos.py           # valida os exemplos contra o schema
├── docs/                       # documentação do projeto
├── src/                        # pastas criadas, ainda sem código
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   ├── api/
│   └── config/
└── tests/                      # pastas criadas, ainda sem testes
    ├── unit/
    ├── integration/
    └── contract/
```

**Ainda a criar** (padrão da plataforma SIG-Log): `LICENSE`, `Dockerfile`, `docker-compose.yml`, `.github/workflows/` (CI/CD), `data/`, `scripts/` e `monitoring/` (Prometheus e Grafana).

## 9. Como executar

Por enquanto, o que pode ser executado é a validação dos contratos de eventos.

```bash
git clone https://github.com/ViniciusNascimento99/Projeto-WMS-.git
cd Projeto-WMS-

pip install -r requirements.txt jsonschema
python testar_eventos.py
```

Saída esperada: os 7 eventos de exemplo aparecem como `OK` e o teste negativo (evento sem `shipmentId`) aparece como `falhou como esperado`.

> A execução da API e do ambiente com Docker Compose será documentada quando forem implementados.

## 10. Testes

| Tipo                                     | Situação                                                                                             |
| ---------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| Contrato de eventos                      | `testar_eventos.py` valida os exemplos contra o schema e confirma que um evento inválido é rejeitado |
| Unitários                                | Pasta `tests/unit` criada, sem testes ainda                                                          |
| Integração (API + banco, API + RabbitMQ) | Pasta `tests/integration` criada, sem testes ainda                                                   |
| Contrato entre módulos                   | Pasta `tests/contract` criada, sem testes ainda                                                      |

## 11. Status do projeto

- [x] Contrato da API (`openapi.yaml`)
- [x] Schema e exemplos de eventos
- [x] Topologia do RabbitMQ (exchanges, filas, bindings e DLQs)
- [x] Validação dos eventos (`testar_eventos.py`)
- [x] Estrutura de pastas `src/` e `tests/` (ainda sem código)
- [x] Documentação em `docs/` (visão, requisitos, personas, DDD, context map, ADRs...)
- [ ] Código-fonte (implementação em `src/`)
- [ ] Dockerfile e Docker Compose
- [ ] Pipeline CI/CD (GitHub Actions)
- [ ] Testes automatizados (unitário, integração, contrato)
- [ ] Observabilidade (logs, métricas, traces, Grafana)
- [ ] DevSecOps (SonarQube, Trivy) e teste de carga (K6)
- [ ] Relatório ATAM
- [ ] Release v1.0.0

## 12. Equipe

Repositório: [@ViniciusNascimento99](https://github.com/ViniciusNascimento99)

| Nome              |
| ----------------- |
| Vinicius Taiguara |
| José Victor       |
| José Jackson      |

---

Projeto acadêmico da disciplina de Análise de Sistemas II.
