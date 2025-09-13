# PDV3 Backend - Railway Deploy Guide

## 🚀 Deploy no Railway

### 1. Preparação
O backend já está configurado com todos os arquivos necessários:
- ✅ `Procfile` - Comando de inicialização
- ✅ `railway.json` - Configuração específica do Railway
- ✅ `nixpacks.toml` - Build configuration
- ✅ `requirements.txt` - Dependências Python
- ✅ `.env.example` - Exemplo de variáveis de ambiente

### 2. Deploy Steps

#### Via Railway CLI:
```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login no Railway
railway login

# Inicializar projeto
railway init

# Deploy
railway up
```

#### Via GitHub:
1. Push o código para um repositório GitHub
2. Conectar o repositório no Railway Dashboard
3. O deploy será automático

### 3. Variáveis de Ambiente no Railway

Configure estas variáveis no Railway Dashboard:

```
DATABASE_URL=postgresql+asyncpg://postgres:sjwnmPdvRKIOuXTFBCyqRmVjEQgGfUzU@interchange.proxy.rlwy.net:50016/railway
JWT_SECRET=a_very_secret_key_that_should_be_changed
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

**Importante**: O Railway fornecerá automaticamente:
- `PORT` - Porta do serviço
- `RAILWAY_ENVIRONMENT=production` - Detectado automaticamente

### 4. PostgreSQL Database

**Usando o banco existente:**
- O backend está configurado para usar o mesmo banco PostgreSQL já existente
- `DATABASE_URL` já configurada: `postgresql+asyncpg://postgres:sjwnmPdvRKIOuXTFBCyqRmVjEQgGfUzU@interchange.proxy.rlwy.net:50016/railway`
- As tabelas serão criadas automaticamente na inicialização se não existirem

### 5. Health Check

O backend inclui endpoint de health check em `/healthz` que o Railway usará para verificar se o serviço está funcionando.

### 6. CORS Configuration

O CORS está configurado para aceitar todas as origens (`allow_origins=["*"]`) para permitir que o cliente PDV3 se conecte de qualquer local.

## 🔧 Estrutura de Deploy

```
backend/
├── app/                 # Código da aplicação
├── Procfile            # Comando de start
├── railway.json        # Config Railway
├── nixpacks.toml       # Build config
├── requirements.txt    # Dependências
├── .env.example        # Exemplo de env vars
└── README_DEPLOY.md    # Este arquivo
```

## 📝 Notas

- O backend detecta automaticamente se está rodando no Railway
- Logs são automaticamente capturados pelo Railway
- O serviço reinicia automaticamente em caso de falha
- Health checks garantem que o serviço está funcionando

## 🌐 URL do Serviço

Após o deploy, o Railway fornecerá uma URL como:
`https://your-service-name.railway.app`

Esta URL deve ser usada no cliente PDV3 como `BACKEND_URL`.
