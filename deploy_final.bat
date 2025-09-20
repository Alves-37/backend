@echo off
echo Fazendo commit e push das correções finais...
echo.

cd /d "c:\Users\saide\sinc\backend"

echo 1. Adicionando arquivos...
git add .

echo 2. Fazendo commit...
git commit -m "fix: corrigir todas as issues de deploy - entry point, asyncpg, healthcheck"

echo 3. Fazendo push...
git push origin main

echo.
echo ✅ Deploy finalizado!
echo.
echo Backend deployado em: https://backend-production-3b13.up.railway.app
echo.
echo Próximos passos:
echo - Testar endpoints da API
echo - Configurar cliente PDV3 com a nova URL
echo.
pause
