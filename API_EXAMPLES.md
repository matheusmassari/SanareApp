# Exemplos de Requisições para a API SanareApp

## Informações Básicas

- **Base URL**: `http://localhost:8000`
- **API Version**: `/api/v1`
- **Documentação Swagger**: `http://localhost:8000/docs`
- **Documentação ReDoc**: `http://localhost:8000/redoc`

## 🏗️ Arquitetura da Aplicação

A SanareApp roda em **3 containers Docker separados**:

| Container | Serviço | Porta | Função |
|-----------|---------|-------|---------|
| `sanare_api` | FastAPI | 8000 | API REST |
| `sanare_db` | PostgreSQL | 5432 | Banco de dados |
| `sanare_pgadmin` | pgAdmin | 5050 | Interface de administração |

**📋 Verificar se todos os serviços estão rodando:**
```bash
docker ps
```

**🔍 Para mais detalhes sobre a arquitetura, consulte:** [`ARCHITECTURE.md`](./ARCHITECTURE.md)

## 1. Health Check

**GET** `http://localhost:8000/health`

```json
{
  "status": "healthy",
  "service": "SanareApp",
  "version": "1.0.0"
}
```

## 2. Cadastro de Usuário

**POST** `http://localhost:8000/api/v1/users/register`

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "email": "usuario@exemplo.com",
  "username": "joao_silva",
  "password": "senha123",
  "full_name": "João Silva"
}
```

**Resposta esperada:**
```json
{
  "id": 1,
  "email": "usuario@exemplo.com",
  "username": "joao_silva",
  "full_name": "João Silva",
  "is_active": true,
  "role": "USER",
  "created_at": "2024-01-01T12:00:00Z"
}
```

## 3. Login de Usuário

**POST** `http://localhost:8000/api/v1/users/login`

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "email": "usuario@exemplo.com",
  "password": "senha123"
}
```

**Resposta esperada:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

## 4. Obter Perfil do Usuário Atual

**GET** `http://localhost:8000/api/v1/users/me`

**Headers:**
```
Authorization: Bearer {seu_token_aqui}
```

**Resposta esperada:**
```json
{
  "id": 1,
  "email": "usuario@exemplo.com",
  "username": "joao_silva",
  "full_name": "João Silva",
  "is_active": true,
  "role": "USER",
  "created_at": "2024-01-01T12:00:00Z"
}
```

## 5. Atualizar Perfil do Usuário

**PUT** `http://localhost:8000/api/v1/users/me`

**Headers:**
```
Authorization: Bearer {seu_token_aqui}
Content-Type: application/json
```

**Body:**
```json
{
  "full_name": "João Silva Santos"
}
```

## 6. Atualizar Senha

**PUT** `http://localhost:8000/api/v1/users/me/password`

**Headers:**
```
Authorization: Bearer {seu_token_aqui}
Content-Type: application/json
```

**Body:**
```json
{
  "current_password": "senha123",
  "new_password": "novaSenha456"
}
```

## 7. Listar Usuários (Admin apenas)

**GET** `http://localhost:8000/api/v1/users/?skip=0&limit=10`

**Headers:**
```
Authorization: Bearer {token_do_admin}
```

## Como Testar no Postman/Insomnia

### 1. Cadastro de Usuário
1. Crie uma requisição POST para `/api/v1/users/register`
2. Adicione o corpo JSON com email, password e full_name
3. Execute a requisição

### 2. Login
1. Crie uma requisição POST para `/api/v1/users/login`
2. Use o mesmo email e senha do cadastro
3. Copie o `access_token` da resposta

### 3. Requisições Autenticadas
1. Para qualquer endpoint que precise de autenticação
2. Adicione o header: `Authorization: Bearer {access_token}`
3. Substitua `{access_token}` pelo token obtido no login

### 4. Criar Usuário Admin
Para testar endpoints administrativos, você pode usar o script:
```bash
docker exec -it sanare_api python scripts/create_admin.py
```

## Códigos de Status HTTP

- **200**: Sucesso
- **201**: Criado com sucesso
- **400**: Erro na requisição
- **401**: Não autorizado
- **403**: Proibido
- **404**: Não encontrado
- **422**: Erro de validação
- **500**: Erro interno do servidor 