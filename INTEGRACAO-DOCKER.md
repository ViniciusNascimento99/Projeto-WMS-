# SIG-Log WMS — integração do front-end

## Arquivos

- `frontend/`: interface web estática, desenvolvida com HTML, CSS e JavaScript.
- `frontend/Dockerfile`: configuração para construir o contêiner do front-end.
- `frontend/nginx.conf`: configuração do Nginx para servir a interface e encaminhar requisições à API.
- `docker-compose.yml`: configuração dos serviços da aplicação, incluindo API, RabbitMQ e front-end.

## Como executar

1. Certifique-se de que o Docker Desktop esteja em execução.
2. Na raiz do repositório, execute:

   `docker compose config --quiet`

3. Inicie os serviços:

   `docker compose up -d --build`

4. Acesse a interface:

   `http://localhost:8080`

A API fica disponível em `http://localhost:8001`.

## Integração com a API

O Nginx entrega a interface e encaminha as requisições iniciadas em `/api/` para o serviço `api:8000` dentro da rede Docker.

## Autenticação

A API exige autenticação JWT e não possui endpoint de login por usuário e senha. Por isso, a tela solicita um token JWT válido.

Não coloque o segredo `JWT_SECRET` no navegador. Utilize apenas um token válido gerado pelo mecanismo de desenvolvimento do projeto.

## Limitações identificadas

A interface utiliza as rotas existentes da API. Funcionalidades sem endpoints disponíveis não são simuladas como operações reais.