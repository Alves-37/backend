@echo off
echo Configurando variaveis de ambiente no Railway...
echo.

echo 1. Configurando DATABASE_URL (host interno - uso dentro do Railway)...
railway variables set DATABASE_URL="postgresql+asyncpg://postgres:yjZJwfkbcNTlNUNQUjbHoRpUtVtGVkpQ@postgres.railway.internal:5432/railway"

echo 2. Configurando DATABASE_PUBLIC_URL (proxy publico - uso local)...
railway variables set DATABASE_PUBLIC_URL="postgresql://postgres:yjZJwfkbcNTlNUNQUjbHoRpUtVtGVkpQ@gondola.proxy.rlwy.net:20145/railway"

echo 3. Configurando JWT_SECRET...
railway variables set JWT_SECRET="a_very_secret_key_that_should_be_changed"

echo 4. Configurando JWT_ALGORITHM...
railway variables set JWT_ALGORITHM="HS256"

echo 5. Configurando ACCESS_TOKEN_EXPIRE_MINUTES...
railway variables set ACCESS_TOKEN_EXPIRE_MINUTES="60"

echo.
echo ✅ Todas as variaveis foram configuradas!
echo.
echo Para verificar as variaveis configuradas:
echo railway variables

echo.
echo Para fazer redeploy com as novas variaveis:
echo railway up --detach

pause
