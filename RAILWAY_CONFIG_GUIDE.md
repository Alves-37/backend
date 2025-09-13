# 🚀 Guia de Configuração de Variáveis no Railway

## Método 1: Via Dashboard (Mais Fácil)

### Passo a Passo:

1. **Acesse o Railway Dashboard:**
   - Vá para: https://railway.app
   - Faça login na sua conta
   - Selecione o projeto do seu backend PDV3

2. **Encontre as Variáveis:**
   - Clique no seu serviço (projeto backend)
   - Procure pela aba **"Variables"** ou **"Environment Variables"**
   - Clique nela

3. **Adicione Cada Variável:**
   
   **DATABASE_URL:**
   ```
   Nome: DATABASE_URL
   Valor: postgresql+asyncpg://postgres:sjwnmPdvRKIOuXTFBCyqRmVjEQgGfUzU@interchange.proxy.rlwy.net:50016/railway
   ```
   
   **JWT_SECRET:**
   ```
   Nome: JWT_SECRET
   Valor: a_very_secret_key_that_should_be_changed
   ```
   
   **JWT_ALGORITHM:**
   ```
   Nome: JWT_ALGORITHM
   Valor: HS256
   ```
   
   **ACCESS_TOKEN_EXPIRE_MINUTES:**
   ```
   Nome: ACCESS_TOKEN_EXPIRE_MINUTES
   Valor: 60
   ```

4. **Salvar:**
   - Clique em **"Add"** ou **"Save"** para cada variável
   - O Railway automaticamente fará redeploy

## Método 2: Via Railway CLI

### Comandos:

```bash
# 1. Navegar para pasta do backend
cd c:\Users\saide\sinc\backend

# 2. Configurar variáveis uma por uma
railway variables set DATABASE_URL="postgresql+asyncpg://postgres:sjwnmPdvRKIOuXTFBCyqRmVjEQgGfUzU@interchange.proxy.rlwy.net:50016/railway"

railway variables set JWT_SECRET="a_very_secret_key_that_should_be_changed"

railway variables set JWT_ALGORITHM="HS256"

railway variables set ACCESS_TOKEN_EXPIRE_MINUTES="60"

# 3. Verificar se foram configuradas
railway variables

# 4. Fazer redeploy (se necessário)
railway up --detach
```

## ✅ Verificação

### Como saber se funcionou:

1. **Via Dashboard:**
   - As variáveis devem aparecer na lista
   - Status do deploy deve ser "Success"

2. **Via CLI:**
   ```bash
   railway variables
   ```

3. **Testando o Backend:**
   - Acesse: `https://seu-projeto.railway.app/healthz`
   - Deve retornar: `{"status": "ok"}`

## 🔧 Script Automático

Execute o arquivo `configure_railway_vars.bat` para configurar todas as variáveis automaticamente via CLI.

## ⚠️ Importante

- **Nunca** exponha essas variáveis publicamente
- O `JWT_SECRET` deve ser alterado para algo mais seguro em produção
- O Railway fornece automaticamente as variáveis `PORT` e `RAILWAY_ENVIRONMENT`
- Após configurar, o backend fará redeploy automaticamente

## 🌐 Próximos Passos

1. Configurar as variáveis
2. Aguardar o redeploy completar
3. Testar os endpoints do backend
4. Configurar a URL do backend no cliente PDV3
