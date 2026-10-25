# Projeto-WMS-

# SIG-Log WMS — Gestão de Estoque e Centro de Distribuição

> **Squad 01** · Plataforma **SIG-Log** (Sistema de Informações Gerenciais de Logística Multimodal)
> Disciplina: Análise de Sistemas II

## 1. Sobre o projeto

O **SIG-Log WMS** é o módulo responsável por gerenciar o fluxo físico de mercadorias dentro dos Centros de Distribuição (CDs) de uma grande empresa logística nacional.

Ele é um dos seis módulos da plataforma SIG-Log, que se integram por **APIs REST** e **mensageria (RabbitMQ)**:

| Módulo | Responsabilidade |
|---|---|
| **WMS & Estoque/CD** (este repositório) | Recebimento, armazenagem, picking, packing e expedição |
| Frota/Modais & Roteirização | Veículos, modais e rotas |
| Rastreamento de Cargas & Telemetria IoT | Tracking e sensores |
| Financeiro & Faturamento | Cobrança e faturamento |
| RH/Jornada & Escalonamento | Jornada e escalas |
| CRM/SAC & Portal do Cliente | Atendimento e portal do cliente |

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

| Código | Caso de uso |
|---|---|
| UC01 | Receber mercadoria |
| UC02 | Conferir mercadoria |
| UC03 | Criar endereço de armazenamento |
| UC04 | Alocar produto |
| UC05 | Consultar estoque |
| UC06 | Gerar ordem de picking |
| UC07 | Registrar separação |
| UC08 | Embalar pedido |
| UC09 | Expedir carga |
| UC10 | Atualizar saldo de estoque |

### Requisitos funcionais

| Código | Descrição |
|---|---|
| RF01 | Cadastro de produtos |
| RF02 | Cadastro de posições |
| RF03 | Registro de recebimento |
| RF04 | Atualização do estoque |
| RF05 | Endereçamento |
| RF06 | Picking |
| RF07 | Packing |
| RF08 | Expedição |
| RF09 | Consulta de estoque |
| RF10 | Histórico de movimentações |

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
- **Integração síncrona:** REST, conforme o contrato [`openapi.yaml`](./openapi.yaml).
- **Integração assíncrona:** eventos via RabbitMQ, conforme [`events.schema.json`](./events.schema.json) e [`rabbitmq-definitions.json`](./rabbitmq-definitions.json).

> A implementação (`src/`) ainda não foi iniciada. Hoje o repositório contém os **contratos** de API e de eventos.

## 5. Contrato da API

Definido em [`openapi.yaml`](./openapi.yaml) (OpenAPI 3.0.3, versão 1.0.0).

- **Base URL (desenvolvimento):** `http://localhost:8001/api/v1`
- **Autenticação:** Bearer JWT

| Método | Endpoint | Descrição | Caso de uso / RF |
|---|---|---|---|
| POST | `/products` | Cadastrar produto | RF01 |
| GET | `/products/{id}` | Consultar produto | — |
| POST | `/addresses` | Criar endereço de armazenamento | UC03, RF02 |
| POST | `/receipts` | Registrar recebimento de mercadoria | UC01, RF03 |
| POST | `/receipts/{id}/conference` | Conferir mercadoria recebida | UC02 |
| POST | `/allocations` | Alocar produto em um endereço | UC04, RF05 |
| GET | `/inventory` | Consultar estoque | UC05, RF09 |
| GET | `/inventory/{product_id}` | Saldo de um produto por endereço | — |
| GET | `/inventory/{product_id}/movements` | Histórico de movimentações | RF10 |
| POST | `/picking` | Gerar ordem de picking | UC06, RF06 |
| POST | `/picking/{id}/pick` | Registrar separação de itens | UC07 |
| POST | `/packing` | Embalar pedido separado | UC08, RF07 |
| POST | `/shipments` | Expedir carga | UC09, RF08 |
| GET | `/shipments/{id}` | Consultar expedição | — |

## 6. Eventos e mensageria

### Eventos publicados pelo WMS

Todos os eventos seguem o schema [`events.schema.json`](./events.schema.json) (JSON Schema 2020-12) e carregam os campos comuns `event`, `version`, `eventId`, `timestamp`, `correlationId` e `source`.

| Evento | Routing key | Quando ocorre |
|---|---|---|
| `MercadoriaRecebida` | `wms.mercadoria.recebida.v1` | Conferência concluída sem divergência |
| `ProdutoArmazenado` | `wms.produto.armazenado.v1` | Produto é alocado em um endereço |
| `EstoqueAtualizado` | `wms.estoque.atualizado.v1` | Saldo de estoque é alterado |
| `PickingCriado` | `wms.picking.criado.v1` | Ordem de picking é gerada |
| `PedidoSeparado` | `wms.pedido.separado.v1` | Todos os itens do pedido foram separados |
| `PedidoEmbalado` | `wms.pedido.embalado.v1` | Embalagem concluída |
| `CargaExpedida` | `wms.carga.expedida.v1` | Carga sai do CD |

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

Definida em [`rabbitmq-definitions.json`](./rabbitmq-definitions.json) (RabbitMQ 3.13, filas do tipo *quorum*, com *dead-letter queue* para cada fila).

**Exchange de saída:** `siglog.wms.events` (topic). Filas dos consumidores:

| Fila | Módulo | Eventos recebidos |
|---|---|---|
| `tracking.wms.events` | Tracking | MercadoriaRecebida, ProdutoArmazenado, CargaExpedida |
| `financeiro.wms.events` | Financeiro | MercadoriaRecebida, EstoqueAtualizado, CargaExpedida |
| `crm.wms.events` | CRM | PickingCriado, PedidoSeparado, PedidoEmbalado, CargaExpedida |
| `frota.wms.events` | Frota | PedidoEmbalado, CargaExpedida |

**Mensagens que o WMS consome:**

| Fila | Origem | Mensagem |
|---|---|---|
| `wms.pedidos.inbox` | `siglog.crm.events` | `crm.pedido.criado.v1` |
| `wms.coletas.inbox` | `siglog.frota.events` | `frota.coleta.agendada.v1` |

Mensagens rejeitadas vão para o exchange `siglog.wms.dlx`, que as encaminha para as filas `*.dlq`.

## 7. Tecnologias

| Área | Tecnologia | Situação |
|---|---|---|
| Linguagem / API | Python, FastAPI, Uvicorn | Dependências listadas em `requirements.txt` |
| Contratos | OpenAPI 3.0.3, JSON Schema 2020-12 | Em uso |
| Mensageria | RabbitMQ | Topologia definida |
| Banco de dados | PostgreSQL | Planejado |
| Contêineres | Docker e Docker Compose | Planejado |
| CI/CD | GitHub Actions | Planejado |
| Observabilidade | OpenTelemetry, Prometheus, Grafana, Jaeger | Planejado |
| Qualidade e segurança | SonarQube, Trivy | Planejado |
| Teste de carga | K6 | Planejado |

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
└── testar_eventos.py           # valida os exemplos contra o schema
```

**Estrutura alvo** (padrão da plataforma SIG-Log): `LICENSE`, `Dockerfile`, `docker-compose.yml`, `.github/workflows/` (CI/CD), `docs/`, `src/` (`domain`, `application`, `infrastructure`, `api`, `config`), `tests/` (`unit`, `integration`, `contract`), `data/`, `scripts/` e `monitoring/` (Prometheus e Grafana).

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

| Tipo | Situação |
|---|---|
| Contrato de eventos | `testar_eventos.py` valida os exemplos contra o schema e confirma que um evento inválido é rejeitado |
| Unitários | Planejado (`tests/unit`) |
| Integração (API + banco, API + RabbitMQ) | Planejado (`tests/integration`) |
| Contrato entre módulos | Planejado (`tests/contract`) |

## 11. Status do projeto

- [x] Contrato da API (`openapi.yaml`)
- [x] Schema e exemplos de eventos
- [x] Topologia do RabbitMQ (exchanges, filas, bindings e DLQs)
- [x] Validação dos eventos (`testar_eventos.py`)
- [x] Documentação em `docs/` (visão, requisitos, personas, DDD, context map, ADRs...)
- [ ] Código-fonte (`src/`)
- [ ] Dockerfile e Docker Compose
- [ ] Pipeline CI/CD (GitHub Actions)
- [ ] Testes automatizados (unitário, integração, contrato)
- [ ] Observabilidade (logs, métricas, traces, Grafana)
- [ ] DevSecOps (SonarQube, Trivy) e teste de carga (K6)
- [ ] Relatório ATAM
- [ ] Release v1.0.0

## 12. Equipe

Repositório: [@ViniciusNascimento99](https://github.com/ViniciusNascimento99)

| Nome |
|---|---|
| _ Vinicius Taiguara_ |
| _ José Victor_ |
| _ José Jackson_ |

---

Projeto acadêmico da disciplina de Análise de Sistemas II.
