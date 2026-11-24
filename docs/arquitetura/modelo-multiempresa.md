# SIG-Log WMS — Modelo de Arquitetura Multiempresa

**Status:** Em definição  
**Banco de dados:** PostgreSQL (Neon)  
**Arquitetura:** SaaS multiempresa  
**Schema principal:** `wms`

## 1. Objetivo

O SIG-Log WMS será desenvolvido como uma plataforma SaaS capaz de atender múltiplas empresas utilizando a mesma aplicação e infraestrutura de banco de dados.

Cada empresa terá seus próprios usuários, centros de distribuição, produtos, estoques, recebimentos, movimentações, pedidos e expedições.

O sistema deverá garantir o isolamento dos dados entre empresas.

## 2. Modelo multiempresa

- Múltiplas empresas utilizarão a mesma plataforma.
- Os dados serão armazenados em um banco PostgreSQL compartilhado.
- Cada empresa terá um identificador exclusivo (`empresa_id`).
- As tabelas operacionais deverão ser vinculadas à empresa proprietária dos registros.
- Uma empresa não poderá consultar ou modificar dados pertencentes a outra.

## 3. Cadastro de empresas

O sistema permitirá duas formas de cadastro:

1. **Cadastro administrativo:** o administrador global da plataforma poderá cadastrar uma empresa e seu primeiro administrador.
2. **Autocadastro:** a própria empresa poderá solicitar seu cadastro na plataforma.

Empresas cadastradas por autocadastro deverão permanecer com status pendente até a aprovação ou validação definida pela plataforma.

## 4. Usuários e empresas

- Cada usuário pertencerá a exatamente uma empresa.
- Um usuário não poderá alternar entre empresas utilizando a mesma conta.
- O vínculo entre usuário e empresa será controlado pelo sistema.
- O identificador da empresa será obtido a partir da identidade autenticada, nunca confiado diretamente ao corpo da requisição.

## 5. Centros de distribuição

- Cada empresa poderá possuir vários centros de distribuição (CDs).
- Todos os funcionários de uma empresa poderão acessar todos os CDs pertencentes àquela empresa.
- O acesso aos CDs não será limitado individualmente por usuário.
- As permissões de operações continuarão dependendo do perfil e das regras de autorização.

## 6. Isolamento e segurança

A arquitetura deverá utilizar:

- `empresa_id` para identificar a propriedade dos registros.
- PostgreSQL Row-Level Security (RLS) para reforçar o isolamento.
- Chaves estrangeiras compostas quando necessário para impedir relacionamentos entre empresas diferentes.
- Autenticação baseada em tokens JWT.
- Validação de permissões na API.
- Transações para preservar a integridade dos dados.

## 7. Persistência

O PostgreSQL hospedado no Neon será o banco de dados oficial da aplicação.

Os dados deverão permanecer disponíveis mesmo após reinicializações ou substituições do container da API.

O armazenamento em memória será utilizado somente em testes ou situações explicitamente definidas para desenvolvimento.

## 8. Capacidade de armazenamento

A capacidade dos endereços será controlada por:

- Quantidade de unidades.
- Peso total em quilogramas (kg).

A dimensão de volume em metros cúbicos (m³) não será utilizada no cálculo de capacidade nem exigida nos cadastros de produtos ou embalagens.

As caixas e os volumes físicos de expedição continuarão existindo como unidades de embalagem.

## 9. Administração

A plataforma deverá distinguir as responsabilidades administrativas globais das responsabilidades administrativas de cada empresa.

A definição detalhada dos perfis e das permissões administrativas permanece pendente de aprovação.

## 10. Migrações e preservação dos dados

- Alterações na estrutura do banco deverão ser realizadas por migrações incrementais.
- A estrutura atual do Neon está documentada em `estrutura_neon.sql`.
- O dump existente será utilizado como referência, não como script para execução integral em produção.
- Os registros existentes deverão ser preservados durante a evolução da arquitetura.
- A atribuição de registros antigos às empresas deverá ser planejada antes da inclusão obrigatória de `empresa_id`.

## 11. Decisões pendentes

- Definição final dos perfis e permissões administrativas.
- Estrutura de autenticação e gerenciamento de usuários.
- Estratégia de aprovação de empresas.
- Política de migração dos registros existentes.
- Implementação das políticas RLS.
- Estratégia de auditoria e rastreabilidade.

---

**Documento de referência arquitetural do SIG-Log WMS.**
