# Guia de Configuração OAuth - SanareApp

Este guia te ajudará a configurar a autenticação OAuth com Google na SanareApp, seguindo as melhores práticas de segurança.

## 🎯 **Recursos Implementados**

✅ **Autenticação OAuth com Google**
✅ **Login e registro automático**
✅ **Vinculação de contas OAuth a usuários existentes**
✅ **Desvinculação de contas OAuth**
✅ **Gerenciamento de múltiplos providers**
✅ **Segurança robusta com state verification**
✅ **Tokens seguros e refresh tokens**

## 📋 **Pré-requisitos**

- Conta Google Cloud Platform
- Projeto SanareApp configurado (do passo anterior)
- Aplicação rodando localmente ou na EC2

## 🚀 **Passo 1: Configurar Google Cloud Console**

### **1.1. Criar Projeto (se necessário)**

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto ou selecione existente
3. Nome sugerido: `sanareapp-oauth`

### **1.2. Habilitar APIs**

```bash
# Via Google Cloud CLI (opcional)
gcloud services enable googleplus.googleapis.com
gcloud services enable oauth2.googleapis.com
```

Ou via Console:
1. **APIs & Services** → **Library**
2. Buscar e habilitar:
   - Google+ API
   - OAuth2 API

### **1.3. Configurar OAuth Consent Screen**

1. **APIs & Services** → **OAuth consent screen**
2. **Configurações**:
   ```
   User Type: External (para teste) ou Internal (para empresa)
   App name: SanareApp
   User support email: seu-email@example.com
   Developer contact: seu-email@example.com
   ```

3. **Scopes**: Adicionar escopos essenciais:
   ```
   email
   profile
   openid
   ```

4. **Test users** (se External): Adicione emails para teste

### **1.4. Criar Credenciais OAuth**

1. **APIs & Services** → **Credentials**
2. **Create Credentials** → **OAuth 2.0 Client IDs**
3. **Application type**: Web application
4. **Name**: SanareApp OAuth Client
5. **Authorized JavaScript origins**:
   ```
   http://localhost:3000
   http://localhost:8000
   https://your-domain.com (produção)
   ```

6. **Authorized redirect URIs**:
   ```
   http://localhost:3000/auth/callback
   http://localhost:8000/auth/callback
   https://your-domain.com/auth/callback
   ```

7. **Salvar** e anotar:
   - Client ID
   - Client Secret

## 🔧 **Passo 2: Configurar Aplicação**

### **2.1. Atualizar Variáveis de Ambiente**

```bash
# Editar arquivo .env
nano .env
```

**Adicionar configurações OAuth:**

```env
# 🔐 OAUTH CONFIGURATION
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
OAUTH_STATE_SECRET=your_oauth_state_secret_32_chars_min
```

### **2.2. Gerar OAUTH_STATE_SECRET**

```python
# Executar no Python para gerar secret seguro
import secrets
print(secrets.token_urlsafe(32))
```

### **2.3. Instalar Dependências**

```bash
# Ativar ambiente virtual
source venv/bin/activate

# Instalar novas dependências
pip install -r requirements.txt
```

### **2.4. Executar Migração do Banco**

```bash
# Gerar migração para OAuth
alembic revision --autogenerate -m "Add OAuth support"

# Aplicar migração
alembic upgrade head
```

## 🧪 **Passo 3: Testar Implementação**

### **3.1. Iniciar Aplicação**

```bash
# Ambiente local
python main.py

# Ou com uvicorn
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### **3.2. Acessar Documentação**

- **Swagger UI**: http://localhost:8000/docs
- **Endpoints OAuth**: `/api/v1/oauth/`

### **3.3. Testar Fluxo OAuth**

**1. Obter URL de autorização:**

```bash
curl -X POST "http://localhost:8000/api/v1/oauth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "google",
    "redirect_uri": "http://localhost:8000/auth/callback"
  }'
```

**2. Resposta esperada:**

```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/auth?...",
  "state": "encrypted_state_token"
}
```

**3. Processar callback** (após autorização):

```bash
curl -X POST "http://localhost:8000/api/v1/oauth/callback?provider=google&code=AUTHORIZATION_CODE&state=STATE_TOKEN"
```

**4. Resposta esperada:**

```json
{
  "access_token": "jwt_token_here",
  "token_type": "bearer"
}
```

## 🔗 **Passo 4: Integração Frontend**

### **4.1. Fluxo de Autenticação**

**JavaScript/TypeScript exemplo:**

```typescript
// 1. Iniciar OAuth
async function initiateOAuth() {
  const response = await fetch('/api/v1/oauth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      provider: 'google',
      redirect_uri: window.location.origin + '/auth/callback'
    })
  });
  
  const data = await response.json();
  
  // Salvar state no localStorage (importante!)
  localStorage.setItem('oauth_state', data.state);
  
  // Redirecionar para Google
  window.location.href = data.authorization_url;
}

// 2. Processar callback (na página /auth/callback)
async function handleOAuthCallback() {
  const urlParams = new URLSearchParams(window.location.search);
  const code = urlParams.get('code');
  const state = urlParams.get('state');
  
  // Verificar state
  const savedState = localStorage.getItem('oauth_state');
  if (state !== savedState) {
    throw new Error('Invalid state parameter');
  }
  
  // Processar callback
  const response = await fetch(
    `/api/v1/oauth/callback?provider=google&code=${code}&state=${state}`,
    { method: 'POST' }
  );
  
  const data = await response.json();
  
  // Salvar token
  localStorage.setItem('access_token', data.access_token);
  
  // Redirecionar para dashboard
  window.location.href = '/dashboard';
}

// 3. Vincular conta OAuth a usuário existente
async function linkOAuthAccount(accessToken: string) {
  const response = await fetch('/api/v1/oauth/link', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`
    },
    body: JSON.stringify({
      provider: 'google',
      code: 'authorization_code',
      state: 'state_token'
    })
  });
  
  return response.json();
}

// 4. Obter contas OAuth do usuário
async function getOAuthAccounts(accessToken: string) {
  const response = await fetch('/api/v1/oauth/accounts', {
    headers: { 'Authorization': `Bearer ${accessToken}` }
  });
  
  return response.json();
}
```

### **4.2. React Hook Exemplo**

```typescript
// useOAuth.ts
import { useState, useCallback } from 'react';

interface OAuthState {
  isLoading: boolean;
  error: string | null;
}

export function useOAuth() {
  const [state, setState] = useState<OAuthState>({
    isLoading: false,
    error: null
  });

  const initiateGoogleOAuth = useCallback(async () => {
    setState({ isLoading: true, error: null });
    
    try {
      const response = await fetch('/api/v1/oauth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider: 'google',
          redirect_uri: `${window.location.origin}/auth/callback`
        })
      });
      
      if (!response.ok) throw new Error('Failed to initiate OAuth');
      
      const data = await response.json();
      localStorage.setItem('oauth_state', data.state);
      window.location.href = data.authorization_url;
      
    } catch (error) {
      setState({ 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'OAuth failed' 
      });
    }
  }, []);

  return {
    ...state,
    initiateGoogleOAuth
  };
}
```

### **4.3. Componente de Login**

```typescript
// GoogleLoginButton.tsx
import React from 'react';
import { useOAuth } from './useOAuth';

export function GoogleLoginButton() {
  const { isLoading, error, initiateGoogleOAuth } = useOAuth();

  return (
    <div>
      <button 
        onClick={initiateGoogleOAuth}
        disabled={isLoading}
        className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600 disabled:opacity-50"
      >
        {isLoading ? 'Conectando...' : 'Entrar com Google'}
      </button>
      
      {error && (
        <p className="text-red-500 mt-2">{error}</p>
      )}
    </div>
  );
}
```

## 🔐 **Passo 5: Segurança e Melhores Práticas**

### **5.1. Validações Implementadas**

✅ **State Parameter**: Previne CSRF attacks
✅ **Token Expiration**: Tokens têm TTL definido
✅ **Scope Limitation**: Apenas escopos necessários
✅ **Email Verification**: Verifica se email está confirmado
✅ **Provider Validation**: Valida provider antes de processar

### **5.2. Configurações de Produção**

**Variáveis de ambiente produção:**

```env
# Usar secrets reais em produção
GOOGLE_CLIENT_ID=real_production_client_id
GOOGLE_CLIENT_SECRET=real_production_client_secret
OAUTH_STATE_SECRET=super_secure_32_char_secret
```

**Configurar HTTPS:**
- OAuth só funciona com HTTPS em produção
- Certificado SSL válido necessário
- Atualizar redirect URIs no Google Console

### **5.3. Monitoramento**

**Logs importantes para monitorar:**

```python
# Exemplo de logs a implementar
logger.info(f"OAuth login attempted: provider={provider}, user_email={email}")
logger.warning(f"OAuth state validation failed: state={state}")
logger.error(f"OAuth token exchange failed: provider={provider}, error={error}")
```

## 📊 **Passo 6: Endpoints Disponíveis**

### **6.1. Autenticação OAuth**

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/oauth/login` | Iniciar fluxo OAuth |
| POST | `/api/v1/oauth/callback` | Processar callback OAuth |
| GET | `/api/v1/oauth/providers` | Listar providers disponíveis |

### **6.2. Gerenciamento de Contas**

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/oauth/link` | Vincular conta OAuth |
| DELETE | `/api/v1/oauth/unlink` | Desvincular conta OAuth |
| GET | `/api/v1/oauth/accounts` | Listar contas OAuth do usuário |
| GET | `/api/v1/oauth/user/complete` | Usuário com dados OAuth |

### **6.3. Exemplos de Resposta**

**Usuário com OAuth:**

```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "user123",
  "full_name": "John Doe",
  "avatar_url": "https://lh3.googleusercontent.com/...",
  "is_oauth_user": true,
  "email_verified": true,
  "oauth_providers": ["google"],
  "oauth_accounts": [
    {
      "id": 1,
      "provider": "google",
      "provider_user_id": "123456789",
      "provider_user_email": "user@gmail.com",
      "provider_user_name": "John Doe",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

## 🚨 **Troubleshooting**

### **Erro: "OAuth provider not configured"**
- Verificar GOOGLE_CLIENT_ID e GOOGLE_CLIENT_SECRET no .env
- Confirmar que as variáveis estão sendo carregadas

### **Erro: "Invalid redirect URI"**
- Verificar redirect URIs no Google Console
- Certificar que URL exata está autorizada

### **Erro: "Invalid state parameter"**
- Verificar OAUTH_STATE_SECRET
- Confirmar que state está sendo preservado no frontend

### **Erro: "Email already registered"**
- Usuário já existe com esse email
- Use funcionalidade de vincular conta

## ✅ **Checklist de Verificação**

- [ ] Google Cloud Console configurado
- [ ] Credenciais OAuth criadas
- [ ] Variáveis de ambiente configuradas
- [ ] Migração do banco executada
- [ ] Aplicação iniciada sem erros
- [ ] Fluxo OAuth testado
- [ ] Frontend integrado
- [ ] Logs configurados

## 🎯 **Próximos Passos**

Com OAuth configurado, você pode:
1. **Adicionar mais providers** (GitHub, Facebook)
2. **Implementar refresh tokens**
3. **Configurar CI/CD** com OAuth
4. **Adicionar testes automatizados**
5. **Configurar monitoramento avançado**

---

**🎉 Parabéns! Seu sistema agora possui autenticação OAuth robusta e segura!**