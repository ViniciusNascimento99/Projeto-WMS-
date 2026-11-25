.PHONY: local-up local-down local-ps local-logs

COMPOSE_LOCAL = env -u DATABASE_URL docker compose --env-file .env.docker --profile db -f docker-compose.yml -f docker-compose.local.yml

# Inicia a API, PostgreSQL e RabbitMQ
local-up:
	$(COMPOSE_LOCAL) up --build -d

# Para os serviços, preservando os dados
local-down:
	$(COMPOSE_LOCAL) down

# Mostra o estado dos serviços
local-ps:
	$(COMPOSE_LOCAL) ps

# Acompanha os logs dos serviços
local-logs:
	$(COMPOSE_LOCAL) logs -f --tail=100
