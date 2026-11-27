# Projeto-WMS-

# SIG-Log WMS — Gestão de Estoque e Centro de Distribuição

> **Squad 01** · Plataforma **SIG-Log** (Sistema de Informações Gerenciais de Logística Multimodal)  
> Disciplina: Análise de Sistemas II

---

## Sumário

1. Sobre o projeto
2. Problema e objetivo
3. Escopo funcional
4. Arquitetura do sistema
5. Contrato da API
6. Eventos e mensageria
7. Tecnologias
8. Banco de dados
9. Estrutura do repositório
10. Como executar
11. Testes e status do projeto
12. Equipe

---

## 1. Sobre o projeto

O **SIG-Log WMS (Warehouse Management System)** é o módulo responsável por gerenciar o fluxo físico de mercadorias dentro dos Centros de Distribuição (CDs) de uma grande empresa logística nacional.

Ele é um dos seis módulos da plataforma SIG-Log, que se integram por **APIs REST** e **mensageria (RabbitMQ)**:

| Módulo | Responsabilidade |
|---|---|
| **WMS & Estoque/CD** (este repositório) | Recebimento, armazenagem, picking, packing e expedição |
| Frota/Modais & Roteirização | Veículos, modais e rotas |
| Rastreamento de Cargas & Telemetria IoT | Tracking e sensores |
| Financeiro & Faturamento | Cobrança e faturamento |
| RH/Jornada & Escalonamento | Jornada e escalas |
| CRM/SAC & Portal do Cliente | Atendimento e portal do cliente |

Cada Squad é responsável pelo seu domínio (*bounded context*). Os módulos se integram respeitando os contratos de API e o catálogo de eventos publicados.

## 2. Problema e objetivo

**Problema:** gerenciar o fluxo físico de mercadorias dentro dos Centros de Distribuição, desde o recebimento até a expedição.

**Objetivo:** controlar uma carga desde sua entrada no CD até sua saída, garantindo organização, rastreabilidade e controle das movimentações de estoque.

### Fluxo operacional

```text
Recebimento
     ↓
Conferência
     ↓
Endereçamento
     ↓
Armazenagem
     ↓
Picking (Separação)
     ↓
Packing (Embalagem)
     ↓
Expedição
```

## 3. Escopo funcional

**Principais entidades do domínio:**

`Produto` · `Carga` · `Pedido` · `Estoque` · `Localizacao` · `Endereco` · `PickingOrder` · `PackingOrder` · `Expedicao` · `MovimentacaoEstoque`

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

## 4. Arquitetura do sistema

O sistema possui uma arquitetura modular, organizada em camadas e inspirada nos princípios de DDD (Domain-Driven Design).

```text
┌──────────────────────────────────────┐
│             FRONT-END                │
│          HTML / CSS / JS             │
├──────────────────────────────────────┤
│               API                    │
│          FastAPI / REST              │
├──────────────────────────────────────┤
│           APPLICATION                │
│       Serviços e casos de uso        │
├──────────────────────────────────────┤
│              DOMAIN                  │
│       Entidades e regras de negócio  │
├──────────────────────────────────────┤
│          INFRASTRUCTURE              │
│       PostgreSQL / RabbitMQ           │
└──────────────────────────────────────┘
```

**Componentes da arquitetura:**

- **Front-end:** interface web desenvolvida com HTML, CSS e JavaScript.
- **API:** disponibiliza os endpoints REST utilizando FastAPI.
- **Application:** organiza os serviços e operações da aplicação.
- **Domain:** concentra as regras e entidades do negócio.
- **Infrastructure:** responsável pelas integrações com banco de dados e serviços externos.

**Persistência:** PostgreSQL 18, utilizando o padrão *Database-per-Service*, mantendo o banco de dados do WMS separado dos demais módulos da plataforma.

**Integração síncrona:** APIs REST, conforme o contrato definido em [`openapi.yaml`](./openapi.yaml).

**Integração assíncrona:** eventos publicados e consumidos por meio do RabbitMQ, conforme [`events.schema.json`](./events.schema.json) e [`rabbitmq-definitions.json`](./rabbitmq-definitions.json).

## 5. Contrato da API

A API é desenvolvida utilizando FastAPI e possui contrato OpenAPI 3.0.3, disponível em [`openapi.yaml`](./openapi.yaml).

- **Base URL:** `http://localhost:8001/api/v1`
- **Documentação Swagger:** `http://localhost:8001/docs`
- **Documentação ReDoc:** `http://localhost:8001/redoc`
- **Health Check:** `http://localhost:8001/health`
- **Autenticação:** Bearer JWT.

### Endpoints

| Método | Endpoint | Descrição | Caso de uso / RF |
|---|---|---|---|
| POST | `/products` | Cadastrar produto | RF01 |
| GET | `/products/{id}` | Consultar produto | — |
| POST | `/addresses` | Criar endereço de armazenamento | UC03, RF02 |
| POST | `/receipts` | Registrar recebimento | UC01, RF03 |
| POST | `/receipts/{id}/conference` | Conferir mercadoria | UC02 |
| POST | `/allocations` | Alocar produto | UC04, RF05 |
| GET | `/inventory` | Consultar estoque | UC05, RF09 |
| GET | `/inventory/{product_id}` | Consultar saldo por produto | — |
| GET | `/inventory/{product_id}/movements` | Histórico de movimentações | RF10 |
| POST | `/picking` | Gerar ordem de picking | UC06, RF06 |
| POST | `/picking/{id}/pick` | Registrar separação | UC07 |
| POST | `/packing` | Embalar pedido | UC08, RF07 |
| POST | `/shipments` | Expedir carga | UC09, RF08 |
| GET | `/shipments/{id}` | Consultar expedição | — |

### Autenticação

As rotas operacionais exigem um token JWT válido enviado no cabeçalho HTTP:

```http
Authorization: Bearer SEU_TOKEN
```

A interface solicita um token válido para realizar as chamadas protegidas. O segredo `JWT_SECRET` deve permanecer no ambiente do servidor, nunca no código do navegador.

### Estados dos recursos

| Recurso | Estados |
|---|---|
| Recebimento | `AGUARDANDO`, `EM_CONFERENCIA`, `CONFERIDA`, `COM_DIVERGENCIA`, `ARMAZENADA` |
| Ordem de picking | `CRIADA`, `EM_SEPARACAO`, `SEPARADA`, `CANCELADA` |
| Ordem de packing | `CRIADA`, `EM_EMBALAGEM`, `EMBALADA` |
| Expedição | `PLANEJADA`, `EXPEDIDA` |
| Movimentação | `ENTRADA`, `SAIDA`, `AJUSTE` |

## 6. Eventos e mensageria

A comunicação entre os módulos da plataforma SIG-Log é realizada por meio do RabbitMQ.

Os eventos seguem o padrão definido em [`events.schema.json`](./events.schema.json), utilizando JSON Schema 2020-12.

### Eventos publicados pelo WMS

| Evento | Routing key | Quando ocorre |
|---|---|---|
| `MercadoriaRecebida` | `wms.mercadoria.recebida.v1` | Conferência concluída sem divergência |
| `ProdutoArmazenado` | `wms.produto.armazenado.v1` | Produto alocado em um endereço |
| `EstoqueAtualizado` | `wms.estoque.atualizado.v1` | Saldo de estoque alterado |
| `PickingCriado` | `wms.picking.criado.v1` | Ordem de picking gerada |
| `PedidoSeparado` | `wms.pedido.separado.v1` | Itens do pedido separados |
| `PedidoEmbalado` | `wms.pedido.embalado.v1` | Embalagem concluída |
| `CargaExpedida` | `wms.carga.expedida.v1` | Carga sai do CD |

### Exemplo de evento

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

A configuração está definida em [`rabbitmq-definitions.json`](./rabbitmq-definitions.json).

**Exchange de saída:** `siglog.wms.events` (topic).

| Fila | Módulo | Eventos recebidos |
|---|---|---|
| `tracking.wms.events` | Tracking | MercadoriaRecebida, ProdutoArmazenado, CargaExpedida |
| `financeiro.wms.events` | Financeiro | MercadoriaRecebida, EstoqueAtualizado, CargaExpedida |
| `crm.wms.events` | CRM | PickingCriado, PedidoSeparado, PedidoEmbalado, CargaExpedida |
| `frota.wms.events` | Frota | PedidoEmbalado, CargaExpedida |

**Mensagens consumidas pelo WMS:**

| Fila | Origem | Mensagem |
|---|---|---|
| `wms.pedidos.inbox` | CRM | `crm.pedido.criado.v1` |
| `wms.coletas.inbox` | Frota | `frota.coleta.agendada.v1` |

As mensagens rejeitadas são encaminhadas para o mecanismo de *Dead Letter Queue* (DLQ), permitindo o tratamento de falhas de processamento.

## 7. Tecnologias

| Área | Tecnologia | Utilização |
|---|---|---|
| Linguagem | Python 3.12 | Desenvolvimento do back-end |
| API | FastAPI | Construção dos serviços REST |
| Servidor | Uvicorn | Execução da API |
| Front-end | HTML, CSS e JavaScript | Interface web |
| Servidor web | Nginx | Disponibilização da interface e proxy da API |
| Banco de dados | PostgreSQL 18 | Persistência das informações |
| Migrações | Alembic | Versionamento da estrutura do banco |
| Autenticação | PyJWT | Tokens JWT |
| Mensageria | RabbitMQ 3.13 | Comunicação entre módulos |
| Containerização | Docker | Empacotamento dos serviços |
| Orquestração | Docker Compose | Inicialização do ambiente |
| Testes | Pytest | Testes automatizados |

## 8. Banco de dados

O projeto passou a contar com integração a um banco de dados relacional **PostgreSQL**, responsável por armazenar as informações operacionais do WMS.

A estrutura também possui exportações SQL associadas ao ambiente Neon/PostgreSQL e gerenciamento de alterações estruturais por meio de migrações.

### Organização dos schemas

O banco está organizado em dois schemas principais:

- **`wms`:** concentra as entidades relacionadas às operações logísticas, estoque e armazenagem.
- **`public`:** utilizado pelos recursos de cadastro, empresas, usuários e autenticação da plataforma.

### Principais tabelas do schema `wms`

| Tabela | Responsabilidade |
|---|---|
| `centro_distribuicao` | Cadastro dos Centros de Distribuição |
| `zona` | Organização das áreas internas do CD |
| `endereco` | Posições físicas de armazenagem |
| `produto` | Cadastro e características dos produtos |
| `lote` | Controle de lotes e datas de validade |
| `carga` | Registro das cargas recebidas |
| `recebimento` | Controle dos recebimentos |
| `recebimento_item` | Produtos e quantidades recebidas |
| `alocacao` | Alocação dos produtos nos endereços |
| `estoque` | Controle dos saldos disponíveis e reservados |
| `movimentacao_estoque` | Histórico de entradas, saídas e ajustes |

### Relacionamento simplificado

```text
CENTRO_DISTRIBUICAO
       │
       ├── ZONA
       │     └── ENDERECO
       │            └── ESTOQUE
       │                  ├── PRODUTO
       │                  └── LOTE
       │
       └── CARGA
              └── RECEBIMENTO
                     └── RECEBIMENTO_ITEM
                            ├── PRODUTO
                            ├── LOTE
                            └── ALOCACAO
                                   └── ENDERECO

MOVIMENTACAO_ESTOQUE
       └── Registro das movimentações
```

O banco utiliza recursos de integridade relacional, como chaves primárias, chaves estrangeiras, restrições e índices.

### PostgreSQL local

O PostgreSQL está configurado no Docker Compose utilizando a imagem `postgres:18-alpine`.

As configurações de desenvolvimento são definidas por variáveis de ambiente:

```env
POSTGRES_USER=wms
POSTGRES_PASSWORD=wms_dev
POSTGRES_DB=wms
```

Esses valores são destinados exclusivamente ao ambiente local de desenvolvimento.

### Neon / PostgreSQL remoto

O projeto também possui arquivos SQL exportados da estrutura do banco:

- [`estrutura_neon.sql`](./estrutura_neon.sql)
- [`estrutura_neon_atual.sql`](./estrutura_neon_atual.sql)

Esses arquivos permitem consultar e acompanhar a estrutura exportada do banco.

Para utilizar uma instância PostgreSQL remota, a aplicação deve receber a variável `DATABASE_URL` com a string de conexão correspondente.

### Versionamento com Alembic

O projeto possui configuração do Alembic em [`alembic.ini`](./alembic.ini) e arquivos de migração na pasta [`migrations/`](./migrations/).

Com as dependências de migração instaladas e o banco corretamente configurado, os comandos principais são:

```bash
# Aplicar migrações pendentes
alembic upgrade head

# Consultar versão atual
alembic current

# Consultar histórico
alembic history
```

**Importante:** por segurança, as migrações para bancos remotos são bloqueadas por padrão. Para autorizá-las explicitamente, é necessário configurar:

```env
ALEMBIC_ALLOW_REMOTE=true
DATABASE_MIGRATION_URL=sua_url_de_conexao
```

Antes de executar migrações em ambientes remotos, confirme o banco de destino e mantenha um backup atualizado.

## 9. Estrutura do repositório

A organização atual do projeto segue a seguinte estrutura:

```text
Projeto-WMS-/
│
├── .github/
│   └── workflows/                 # Automações do GitHub Actions
│
├── docs/                          # Documentação complementar
│
├── frontend/
│   ├── Dockerfile                 # Construção do front-end
│   └── nginx.conf                 # Configuração do Nginx
│
├── migrations/                    # Migrações do banco de dados
│
├── src/
│   ├── api/                       # Rotas e controladores
│   ├── application/               # Serviços e casos de uso
│   ├── config/                    # Configurações e segurança
│   ├── domain/                    # Regras e entidades do domínio
│   └── infrastructure/            # Integrações e infraestrutura
│
├── tests/                         # Testes automatizados
│
├── .env.example                   # Variáveis de ambiente
├── Dockerfile                     # Imagem da API
├── docker-compose.yml             # Orquestração dos serviços
├── docker-compose.local.yml       # Configuração complementar
├── alembic.ini                    # Configuração do Alembic
├── criar_admin.py                 # Script auxiliar administrativo
├── estrutura_neon.sql             # Exportação SQL
├── estrutura_neon_atual.sql       # Exportação SQL atualizada
├── events.examples.json           # Exemplos de eventos
├── events.schema.json             # Schema dos eventos
├── INTEGRACAO-DOCKER.md           # Integração do front-end
├── main.py                        # Inicialização da API
├── openapi.yaml                   # Contrato da API
├── rabbitmq-definitions.json      # Configuração do RabbitMQ
├── requirements.txt               # Dependências principais
├── requirements-dev.txt           # Dependências de desenvolvimento
└── README.md                      # Documentação principal
```

## 10. Como executar

### Pré-requisitos

- Git;
- Python 3.12;
- Docker Desktop;
- Docker Compose;
- Navegador atualizado.

### 1. Clonar o repositório

```bash
git clone https://github.com/ViniciusNascimento99/Projeto-WMS-.git

cd Projeto-WMS-
```

### 2. Configurar as variáveis de ambiente

Copie o arquivo `.env.example` e crie seu próprio `.env`.

**Linux / macOS:**

```bash
cp .env.example .env
```

**Windows PowerShell:**

```powershell
Copy-Item .env.example .env
```

O arquivo `.env.example` contém as configurações básicas do PostgreSQL e RabbitMQ.

Defina também um segredo JWT forte no ambiente:

```env
JWT_SECRET=sua_chave_secreta_de_desenvolvimento
```

Não compartilhe o arquivo `.env` nem publique credenciais no GitHub.

### 3. Validar o Docker Compose

```bash
docker compose config --quiet
```

### 4. Construir e iniciar os serviços

```bash
docker compose up -d --build
```

O ambiente inicializa os seguintes serviços:

- API FastAPI;
- Front-end;
- PostgreSQL;
- RabbitMQ;
- Configuração automática das filas e exchanges do RabbitMQ.

### 5. Verificar os serviços

```bash
docker compose ps
```

Para acompanhar os registros de execução:

```bash
docker compose logs -f
```

### 6. Acessar o sistema

| Serviço | Endereço |
|---|---|
| Front-end | http://localhost:8080 |
| API | http://localhost:8001 |
| Swagger | http://localhost:8001/docs |
| ReDoc | http://localhost:8001/redoc |
| Health Check | http://localhost:8001/health |
| RabbitMQ Management | http://localhost:15672 |
| PostgreSQL | localhost:5432 |

### Comandos adicionais

```bash
# Parar os serviços
docker compose down

# Reiniciar os serviços
docker compose restart

# Reconstruir as imagens
docker compose up -d --build

# Visualizar logs da API
docker compose logs -f api

# Remover serviços e volumes
docker compose down -v
```

**Atenção:** o comando `docker compose down -v` remove os volumes persistentes e pode apagar os dados armazenados localmente no PostgreSQL e RabbitMQ.

## 11. Testes e status do projeto

### Testes

O projeto possui configuração para execução de testes automatizados com Pytest.

As dependências de desenvolvimento estão listadas em `requirements-dev.txt`.

Para instalá-las:

```bash
pip install -r requirements-dev.txt
```

Para executar os testes:

```bash
pytest
```

### Status do projeto

- [x] Contrato da API (`openapi.yaml`)
- [x] Implementação da API com FastAPI
- [x] Organização modular em `src/`
- [x] Interface web com HTML, CSS e JavaScript
- [x] Integração do front-end com a API
- [x] Configuração Docker e Docker Compose
- [x] Integração com PostgreSQL
- [x] Estrutura de banco de dados para o domínio WMS
- [x] Exportações SQL do banco de dados
- [x] Configuração de migrações com Alembic
- [x] Configuração de autenticação JWT
- [x] Schema e exemplos de eventos
- [x] Topologia do RabbitMQ
- [x] Configuração de testes com Pytest
- [x] Documentação de integração do Docker
- [ ] Ampliação dos testes automatizados
- [ ] Evolução da integração entre todos os módulos SIG-Log
- [ ] Ampliação da observabilidade
- [ ] Relatório ATAM
- [ ] Release v1.0.0

## 12. Equipe

Repositório: [@ViniciusNascimento99](https://github.com/ViniciusNascimento99)

| Nome |
|---|
| Vinicius Taiguara |
| José Victor |
| José Jackson |

---

Projeto acadêmico da disciplina de **Análise de Sistemas II**.
