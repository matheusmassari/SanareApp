# Configuração do pgAdmin

## Acesso ao pgAdmin

Após executar `docker compose up --build`, você poderá acessar o pgAdmin através do navegador:

- **URL**: `http://localhost:5050`
- **Email**: `admin@sanare.com`
- **Senha**: `admin123`

## Configuração da Conexão com o Banco de Dados

### 1. Primeiro Acesso
1. Abra o navegador e acesse `http://localhost:5050`
2. Faça login com as credenciais acima
3. Clique em "Add New Server" ou no ícone "+" para adicionar um servidor

### 2. Configuração do Servidor PostgreSQL

**Aba General:**
- **Name**: `SanareApp DB` (ou qualquer nome de sua preferência)

**Aba Connection:**
- **Host name/address**: `db` (nome do serviço no docker-compose)
- **Port**: `5432`
- **Maintenance database**: `sanare_db`
- **Username**: `your_database_user` (conforme configurado no .env)
- **Password**: `your_database_password` (conforme configurado no .env)

### 3. Configurações Avançadas (Opcional)

**Aba Advanced:**
- **DB restriction**: `sanare_db` (para mostrar apenas este banco)

**Aba SSL:**
- **SSL mode**: `Prefer` (padrão)

### 4. Salvar Configuração
1. Clique em "Save" para salvar a configuração
2. O servidor aparecerá na lista à esquerda
3. Clique no servidor para expandir e ver o banco de dados

## Explorando o Banco de Dados

### Estrutura do Banco
Após a conexão, você verá:
```
SanareApp DB
├── Databases
│   └── sanare_db
│       ├── Schemas
│       │   └── public
│       │       ├── Tables
│       │       │   ├── users (tabela de usuários)
│       │       │   └── alembic_version (controle de migrações)
│       │       ├── Views
│       │       ├── Functions
│       │       └── Sequences
```

### Visualizar Dados dos Usuários
1. Navegue até: `Databases > sanare_db > Schemas > public > Tables`
2. Clique com o botão direito em `users`
3. Selecione `View/Edit Data > All Rows`

### Executar Consultas SQL
1. Clique com o botão direito no banco `sanare_db`
2. Selecione `Query Tool`
3. Execute consultas como:
```sql
-- Ver todos os usuários
SELECT * FROM users;

-- Contar usuários ativos
SELECT COUNT(*) FROM users WHERE is_active = true;

-- Ver usuários administrativos
SELECT * FROM users WHERE is_admin = true;
```

## Comandos Úteis

### Verificar se o pgAdmin está rodando
```bash
docker ps | grep pgadmin
```

### Logs do pgAdmin
```bash
docker logs sanare_pgadmin
```

### Reiniciar apenas o pgAdmin
```bash
docker restart sanare_pgadmin
```

## Solução de Problemas

### Problema: Não consegue conectar ao banco
**Solução**: Verifique se:
1. O serviço `db` está rodando: `docker ps | grep postgres`
2. Use `db` como hostname (não `localhost`)
3. As credenciais estão corretas conforme o arquivo `.env`

### Problema: pgAdmin não carrega
**Solução**: 
1. Verifique se a porta 5050 está livre
2. Aguarde alguns segundos após o `docker compose up`
3. Verifique os logs: `docker logs sanare_pgadmin`

### Problema: Esqueceu a senha do pgAdmin
**Solução**: Altere a senha no arquivo `.env` e reinicie:
```bash
docker compose down
docker compose up -d pgadmin
```

## Backup e Restore

### Fazer Backup
1. Clique com o botão direito no banco `sanare_db`
2. Selecione `Backup...`
3. Escolha o formato (Custom recomendado)
4. Configure as opções e clique em `Backup`

### Restaurar Backup
1. Clique com o botão direito no banco `sanare_db`
2. Selecione `Restore...`
3. Selecione o arquivo de backup
4. Configure as opções e clique em `Restore` 