# 🚀 Quickstart - SanareApp

## Início em 5 minutos

### 1. Clonar e configurar
```bash
git clone <seu-repositorio>
cd SanareApp

# Configurar variáveis de ambiente
cp env.template .env
```

### 2. Iniciar com Docker
```bash
# Construir e iniciar
docker compose up --build

# Ou usar Make
make dev
```

### 3. Aguardar inicialização
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

### 4. Executar migrações
```bash
# Entrar no container
docker-compose exec api bash

# Criar e aplicar migração
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head

# Ou usar Make
make create-migration name="Initial migration"
make migrate
```

### 5. Criar usuário admin
```bash
# Dentro do container
python scripts/create_admin.py

# Ou usar Make
make create-admin
```

### 6. Testar API
```bash
# Usar script de teste
python test_api.py

# Ou usar Make
make test
```

## Endpoints principais

### Registrar usuário
```bash
curl -X POST "http://localhost:8000/api/v1/users/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "usuario",
    "password": "senha123456",
    "full_name": "Nome Completo"
  }'
```

### Login
```bash
curl -X POST "http://localhost:8000/api/v1/users/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "senha123456"
  }'
```

### Perfil (autenticado)
```bash
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

## Comandos úteis

```bash
# Ver ajuda
make help

# Logs
make logs

# Shell do container
make shell

# Parar serviços
make down

# Limpar tudo
make clean
```

## Estrutura criada

✅ **Backend completo com FastAPI**
✅ **PostgreSQL containerizado**
✅ **Autenticação JWT**
✅ **Migrações com Alembic**
✅ **Docker + Docker Compose**
✅ **Arquitetura modular**
✅ **Documentação automática**
✅ **Scripts de utilidade**
✅ **Makefile para comandos**

## Próximos passos

1. **Personalizar configurações** em `.env`
2. **Criar novos módulos** seguindo o padrão `app/users/`
3. **Adicionar testes** automatizados
4. **Integrar com LLMs** para IA
5. **Configurar CI/CD**
6. **Deploy em produção**

---

🎉 **Seu backend está pronto para uso!** 