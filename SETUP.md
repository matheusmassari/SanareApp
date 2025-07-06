# Setup Completo - SanareApp

## Pré-requisitos

- Docker Desktop instalado e rodando
- Git para clonar o repositório
- Editor de texto (VS Code, Cursor, vim, etc.)

## Configuração Passo a Passo

### 1. Clonar o repositório
```bash
git clone <seu-repositorio>
cd SanareApp
```

### 2. Configurar variáveis de ambiente

O projeto usa um arquivo `.env` para configurar todas as variáveis de ambiente. Isso é mais seguro e flexível.

### 3. Personalizar o arquivo .env

Abra o arquivo `.env` e personalize as configurações:

```bash
# Editar com seu editor preferido
nano .env
# ou
code .env
# ou
vim .env
```

**Configurações importantes:**

```env
# 🔐 SEGURANÇA - SEMPRE ALTERE EM PRODUÇÃO
SECRET_KEY=your-super-secure-secret-key-at-least-32-characters-long
POSTGRES_PASSWORD=your_secure_database_password_here

# 🛠️ DESENVOLVIMENTO
DEBUG=true

# 🚀 PRODUÇÃO
DEBUG=false
```

### 4. Verificar Docker

```bash
# Verificar se Docker está rodando
docker --version
docker compose --version

# Deve retornar as versões sem erro
```

### 5. Iniciar a aplicação

```bash
# Construir e iniciar todos os serviços
docker compose up --build

# Aguardar as mensagens de sucesso:
# ✅ Database initialized
# ✅ Application startup complete
```

### 6. Verificar se funcionou

Em outro terminal:

```bash
# Testar endpoint de saúde
curl http://localhost:8000/health

# Resposta esperada:
# {"status":"healthy","service":"SanareApp","version":"1.0.0"}
```

### 7. Acessar a documentação

- **API Principal**: http://localhost:8000
- **Documentação Swagger**: http://localhost:8000/docs
- **Documentação ReDoc**: http://localhost:8000/redoc

### 8. Configurar banco de dados

```bash
# Entrar no container da API
docker compose exec api bash

# Criar primeira migração
alembic revision --autogenerate -m "Initial migration"

# Aplicar migração
alembic upgrade head

# Sair do container
exit
```

### 9. Criar usuário administrador

```bash
# Executar script de criação
docker compose exec api python scripts/create_admin.py

# Credenciais padrão:
# Email: admin@sanareapp.com
# Senha: admin123456 (MUDE IMEDIATAMENTE!)
```

### 10. Testar API completa

```bash
# Executar testes automatizados
python test_api.py
```

### Configuração para Desenvolvimento

```env
# Configurações para desenvolvimento local
DEBUG=true
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8080,http://127.0.0.1:3000
```

## Comandos Úteis

```bash
# Ver logs em tempo real
docker compose logs -f

# Parar serviços
docker compose down

# Reiniciar serviços
docker compose restart

# Limpar tudo e recomeçar
docker compose down -v
docker compose up --build

# Acessar shell do container
docker compose exec api bash

# Ver status dos serviços
docker compose ps
```

## Troubleshooting

### Problema: Variáveis não carregadas
**Solução**: Verificar se o arquivo `.env` existe e está no diretório raiz

### Problema: Porta em uso
**Solução**: `kill -9 $(lsof -ti:8000)` ou alterar porta no `.env`

### Problema: Docker não conecta
**Solução**: Verificar se Docker Desktop está rodando

### Problema: Permissões
**Solução**: `chmod -R 755 .` no diretório do projeto

## Próximos Passos

1. ✅ **Personalizar configurações** no arquivo `.env`
2. ✅ **Testar todos os endpoints** com a documentação
3. ✅ **Criar usuário admin** e testar autenticação
4. 🔄 **Desenvolver novos módulos** seguindo a estrutura
5. 🔄 **Integrar com LLMs** para funcionalidades de IA
6. 🔄 **Configurar CI/CD** para deploy automático

---

🎉 **Parabéns! Sua aplicação está configurada e pronta para uso!** 