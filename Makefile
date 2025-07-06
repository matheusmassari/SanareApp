.PHONY: help build up down logs shell test clean migrate create-admin

help: ## Mostrar ajuda
	@echo "Comandos disponíveis:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Construir as imagens Docker
	docker compose build

up: ## Iniciar os serviços
	docker compose up -d

down: ## Parar os serviços
	docker compose down

logs: ## Mostrar logs dos serviços
	docker compose logs -f

shell: ## Acessar shell do container da API
	docker compose exec api bash

test: ## Executar testes da API
	python test_api.py

clean: ## Limpar containers e volumes
	docker compose down -v
	docker system prune -f

migrate: ## Executar migrações do banco
	docker compose exec api alembic upgrade head

create-migration: ## Criar nova migração
	docker compose exec api alembic revision --autogenerate -m "$(name)"

create-admin: ## Criar usuário administrador
	docker compose exec api python scripts/create_admin.py

dev: ## Iniciar ambiente de desenvolvimento
	docker compose up --build

prod: ## Iniciar ambiente de produção
	docker compose -f docker-compose.yml up -d --build

restart: ## Reiniciar serviços
	docker compose restart

status: ## Mostrar status dos serviços
	docker compose ps

install: ## Instalar dependências localmente
	pip install -r requirements.txt

format: ## Formatar código (se black estiver instalado)
	black app/ || echo "Black não encontrado, instale com: pip install black"

lint: ## Verificar código (se flake8 estiver instalado)
	flake8 app/ || echo "Flake8 não encontrado, instale com: pip install flake8" 