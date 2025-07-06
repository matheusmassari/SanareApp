# SanareApp - Modern Backend API

Uma aplicação backend moderna construída com FastAPI, SQLAlchemy, PostgreSQL e Docker. Desenvolvida com arquitetura modular e pronta para escalar.

## Funcionalidades

- **API RESTful** com FastAPI assíncrono
- **Autenticação JWT** completa (login, registro, proteção de rotas)
- **Banco de dados PostgreSQL** com SQLAlchemy async
- **Migrações** automatizadas com Alembic
- **Containerização** completa com Docker
- **Arquitetura modular** por features
- **Sistema de roles** (admin, usuário comum)
- **Validação de dados** com Pydantic
- **Documentação automática** com Swagger/OpenAPI

## Tecnologias

- **Backend**: Python 3.11+, FastAPI
- **Banco de dados**: PostgreSQL 16+
- **ORM**: SQLAlchemy 2.0+ (async)
- **Autenticação**: JWT com python-jose
- **Containerização**: Docker, Docker Compose
- **Migrações**: Alembic
- **Segurança**: bcrypt para hashing de senhas

## 📁 Estrutura do Projeto

```
SanareApp/
├── app/
│   ├── core/                    # Componentes compartilhados
│   │   ├── __init__.py
│   │   ├── config.py           # Configurações da aplicação
│   │   ├── database.py         # Configuração do banco
│   │   ├── security.py         # Funções de segurança
│   │   └── auth.py             # Dependências de autenticação
│   ├── users/                   # Módulo de usuários
│   │   ├── __init__.py
│   │   ├── models.py           # Modelo SQLAlchemy
│   │   ├── schemas.py          # Schemas Pydantic
│   │   ├── routes.py           # Rotas da API
│   │   ├── service.py          # Lógica de negócio
│   │   └── dependencies.py     # Dependências específicas
│   └── __init__.py
├── alembic/                     # Migrações do banco
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
├── main.py                      # Entrada da aplicação
├── requirements.txt             # Dependências Python
├── Dockerfile                   # Imagem Docker da API
├── docker-compose.yml           # Orquestração dos serviços
├── .env                         # Variáveis de ambiente (criar a partir do env.template)
├── env.template                 # Template das variáveis de ambiente
├── alembic.ini                  # Configuração do Alembic
└── README.md
```

## Início Rápido

### Pré-requisitos

- Docker e Docker Compose instalados
- Git (para clonar o repositório)

### 1. Clonar o repositório

```bash
git clone <seu-repositorio>
cd SanareApp
```

### 2. Configurar variáveis de ambiente

Copie o arquivo de exemplo e configure as variáveis:

```bash
# Copiar arquivo de exemplo
cp env.template .env

# Editar as variáveis conforme necessário
nano .env  # ou vim .env, code .env, etc.
```

**Importante:** Para produção, altere pelo menos estas variáveis:

```env
# Exemplo de configuração para produção
SECRET_KEY=your-super-secure-secret-key-at-least-32-characters-long
POSTGRES_PASSWORD=your_secure_database_password_here
DEBUG=false
```

### 3. Iniciar a aplicação

```bash
# Construir e iniciar os serviços
docker compose up --build

# Ou em modo detached (background)
docker compose up -d --build
```

A aplicação estará disponível em:
- **API**: http://localhost:8000
- **Documentação**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 4. Executar migrações

```bash
# Entrar no container da API
docker compose exec api bash

# Gerar primeira migração
alembic revision --autogenerate -m "Initial migration"

# Aplicar migrações
alembic upgrade head
```

## 📋 Endpoints da API

### Autenticação
- `POST /api/v1/users/register` - Registrar novo usuário
- `POST /api/v1/users/login` - Login do usuário

### Perfil do usuário
- `GET /api/v1/users/me` - Obter perfil atual
- `PUT /api/v1/users/me` - Atualizar perfil atual
- `PUT /api/v1/users/me/password` - Alterar senha

### Gerenciamento de usuários (Admin)
- `GET /api/v1/users/` - Listar usuários
- `GET /api/v1/users/{id}` - Obter usuário específico
- `PUT /api/v1/users/{id}` - Atualizar usuário
- `DELETE /api/v1/users/{id}` - Deletar usuário

### Utilidade
- `GET /health` - Health check
- `GET /` - Informações da API

## Documentação Adicional

- **[Arquitetura da Aplicação](./ARCHITECTURE.md)** - Detalhes completos sobre a arquitetura, containers e comunicação
- **[Exemplos de API](./API_EXAMPLES.md)** - Exemplos práticos de requisições para Postman/Insomnia
- **[Configuração do pgAdmin](./PGADMIN_SETUP.md)** - Como configurar e usar o pgAdmin para gerenciar o banco
- **[Guia de Início Rápido](./QUICKSTART.md)** - Instruções rápidas para começar
- **[Configuração](./SETUP.md)** - Configuração detalhada do ambiente

## Desenvolvimento

### Executar localmente (sem Docker)

```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
export DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/dbname"

# Executar a aplicação
python main.py
```

### Adicionando novos módulos

1. Criar estrutura de pastas:
```bash
mkdir app/posts
touch app/posts/__init__.py
touch app/posts/models.py
touch app/posts/schemas.py
touch app/posts/routes.py
touch app/posts/service.py
touch app/posts/dependencies.py
```

2. Importar no `main.py`:
```python
from app.posts.routes import router as posts_router
app.include_router(posts_router, prefix=f"{settings.API_V1_STR}/posts", tags=["posts"])
```

## 🔐 Autenticação

### Registrar um usuário

```bash
curl -X POST "http://localhost:8000/api/v1/users/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "usuario123",
    "password": "senha123456",
    "full_name": "Nome Completo"
  }'
```

### Fazer login

```bash
curl -X POST "http://localhost:8000/api/v1/users/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "senha123456"
  }'
```

### Usar token nas requisições

```bash
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

## Comandos Docker

```bash
# Construir imagens
docker compose build

# Iniciar serviços
docker compose up

# Parar serviços
docker compose down

# Ver logs
docker compose logs

# Executar comando no container
docker compose exec api python -m pytest

# Resetar banco de dados
docker compose down -v
docker compose up --build
```

## Deploy

### Preparação para produção

1. Altere as variáveis de ambiente:
```env
SECRET_KEY=your-production-secret-key-at-least-32-characters-long
DEBUG=False
POSTGRES_PASSWORD=your_production_database_password
```

2. Configure CORS para seu domínio:
```env
BACKEND_CORS_ORIGINS=https://meusite.com
```

3. Configure proxy reverso (Nginx):
```nginx
server {
    listen 80;
    server_name meusite.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📈 Próximos Passos

- [ ] Integração com LLMs (OpenAI, Claude, etc.)
- [ ] Sistema de tarefas assíncronas (Celery/RQ)
- [ ] Testes automatizados
- [ ] CI/CD Pipeline
- [ ] Monitoramento e logs
- [ ] Cache com Redis
- [ ] Upload de arquivos
- [ ] Notificações em tempo real

## Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature
3. Faça commit das suas alterações
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.