# Arquitetura da Aplicação SanareApp

## Visão Geral

A SanareApp é uma aplicação backend moderna construída com FastAPI e PostgreSQL, totalmente containerizada usando Docker. A aplicação segue uma arquitetura de microserviços com containers separados para cada responsabilidade.

## Containers da Aplicação

A aplicação está dividida em **3 containers distintos**:

### 1. Container do Banco de Dados (`sanare_db`)
- **Imagem**: `postgres:16-alpine`
- **Porta**: `5432:5432`
- **IP interno**: `172.19.0.2`
- **Função**: Banco de dados PostgreSQL
- **Volume**: `postgres_data` para persistência dos dados
- **Healthcheck**: Verificação automática de saúde do banco

### 2. Container da API (`sanare_api`)
- **Imagem**: `sanareapp-api` (construída a partir do Dockerfile)
- **Porta**: `8000:8000`
- **IP interno**: `172.19.0.4`
- **Função**: API REST com FastAPI
- **Volume**: `.:/app` para desenvolvimento com hot-reload
- **Dependência**: Aguarda o banco estar saudável antes de iniciar

### 3. Container do pgAdmin (`sanare_pgadmin`)
- **Imagem**: `dpage/pgadmin4:8.2`
- **Porta**: `5050:80`
- **IP interno**: `172.19.0.3`
- **Função**: Interface web para gerenciar o banco de dados
- **Volume**: `pgadmin_data` para persistência das configurações

## 🌐 Rede Docker

Todos os containers estão conectados na mesma rede Docker chamada `sanareapp_default`, que permite a comunicação entre eles usando os nomes dos serviços como hostnames.

### Comunicação entre Containers

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   sanare_api    │    │   sanare_db     │    │ sanare_pgadmin  │
│  (FastAPI)      │◄──►│  (PostgreSQL)   │◄──►│   (pgAdmin)     │
│  172.19.0.4     │    │  172.19.0.2     │    │  172.19.0.3     │
│  Port: 8000     │    │  Port: 5432     │    │  Port: 5050     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

- **API → Banco**: A API se conecta ao banco usando o hostname `db`
- **pgAdmin → Banco**: O pgAdmin se conecta ao banco também usando o hostname `db`
- **Dependências**: A API só inicia após o banco estar saudável (healthcheck)

## 📊 Vantagens desta Arquitetura

### 1. **Separação de Responsabilidades**
- Cada container tem uma função específica
- Facilita a manutenção e debugging
- Permite atualizações independentes

### 2. **Escalabilidade**
- Cada serviço pode ser escalado independentemente
- Possibilidade de adicionar réplicas conforme necessário
- Load balancing entre instâncias

### 3. **Isolamento**
- Falhas em um container não afetam os outros
- Recursos isolados (CPU, memória, rede)
- Segurança aprimorada

### 4. **Flexibilidade**
- Fácil adição de novos serviços (Redis, Nginx, etc.)
- Troca de tecnologias sem afetar outros componentes
- Ambiente de desenvolvimento idêntico à produção

### 5. **Portabilidade**
- Execução consistente em qualquer ambiente
- Facilita CI/CD
- Reduz problemas de "funciona na minha máquina"

## 🔍 Comandos de Verificação

### Verificar containers em execução
```bash
docker ps
```

### Verificar logs dos containers
```bash
# Logs da API
docker logs sanare_api

# Logs do banco
docker logs sanare_db

# Logs do pgAdmin
docker logs sanare_pgadmin
```

### Verificar a rede Docker
```bash
docker network ls
docker network inspect sanareapp_default
```

### Verificar saúde dos containers
```bash
docker inspect sanare_db | grep -A 10 "Health"
```

## 🌍 Acesso aos Serviços

| Serviço | URL | Porta | Descrição |
|---------|-----|-------|-----------|
| API FastAPI | `http://localhost:8000` | 8000 | Endpoints da API |
| Documentação Swagger | `http://localhost:8000/docs` | 8000 | Documentação interativa |
| Documentação ReDoc | `http://localhost:8000/redoc` | 8000 | Documentação alternativa |
| pgAdmin | `http://localhost:5050` | 5050 | Interface de administração do banco |
| PostgreSQL | `localhost:5432` | 5432 | Conexão direta ao banco (externa) |

## **Inicializando** a Aplicação

### Primeira execução
```bash
# Construir e iniciar todos os containers
docker compose up --build

# Ou em modo detached (background)
docker compose up --build -d
```

### Execuções subsequentes
```bash
# Iniciar containers existentes
docker compose up

# Ou em modo detached
docker compose up -d
```

### Parar a aplicação
```bash
# Parar todos os containers
docker compose down

# Parar e remover volumes (cuidado: apaga dados!)
docker compose down -v
```

## 📈 Monitoramento

### Status dos containers
```bash
# Ver status de todos os containers
docker compose ps

# Ver uso de recursos
docker stats
```

### Logs em tempo real
```bash
# Logs de todos os containers
docker compose logs -f

# Logs de um container específico
docker compose logs -f api
```

## 🔄 Atualizações e Manutenção

### Atualizar apenas a API
```bash
docker compose up --build api
```

### Atualizar apenas o banco
```bash
docker compose up --build db
```

### Backup do banco de dados
```bash
docker exec sanare_db pg_dump -U sanare_user sanare_db > backup.sql
```

### Restore do banco de dados
```bash
docker exec -i sanare_db psql -U sanare_user sanare_db < backup.sql
```

## 🛠️ Desenvolvimento

### Hot Reload
A API está configurada com hot reload, então mudanças no código são automaticamente refletidas sem necessidade de reiniciar o container.

### Debugging
Para fazer debug da aplicação, você pode:
1. Verificar logs: `docker logs sanare_api`
2. Acessar o container: `docker exec -it sanare_api bash`
3. Verificar variáveis de ambiente: `docker exec sanare_api env`****

### Testes
```bash
# Executar testes dentro do container
docker exec sanare_api python -m pytest

# Ou mapear volume para testes locais
docker run --rm -v $(pwd):/app sanareapp-api python -m pytest
```

## 📋 Checklist de Saúde da Aplicação

- [ ] Todos os containers estão rodando (`docker ps`)
- [ ] API responde no health check (`curl http://localhost:8000/health`)
- [ ] Banco de dados está acessível (`docker exec sanare_db pg_isready`)
- [ ] pgAdmin está acessível (`curl http://localhost:5050`)
- [ ] Logs não mostram erros críticos
- [ ] Conexão entre API e banco está funcionando

Esta arquitetura garante uma aplicação robusta, escalável e fácil de manter! 