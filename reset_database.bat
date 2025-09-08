@echo off
echo ========================================
echo    RESET BANCO DE DADOS POSTGRESQL
echo ========================================
echo.
echo Opcoes disponiveis:
echo   1. Verificar conexao
echo   2. Reset completo (APAGA TUDO)
echo   3. Limpar apenas dados
echo   4. Sair
echo.
set /p choice="Escolha uma opcao (1-4): "

if "%choice%"=="1" (
    echo.
    echo Verificando conexao com o banco...
    python reset_database_online.py check
    goto end
)

if "%choice%"=="2" (
    echo.
    echo *** ATENCAO: RESET COMPLETO ***
    echo Esta opcao ira APAGAR TODAS as tabelas e dados!
    echo.
    python reset_database_online.py complete
    goto end
)

if "%choice%"=="3" (
    echo.
    echo *** ATENCAO: LIMPEZA DE DADOS ***
    echo Esta opcao ira APAGAR TODOS os dados mas manter a estrutura!
    echo.
    python reset_database_online.py data
    goto end
)

if "%choice%"=="4" (
    echo Operacao cancelada.
    goto end
)

echo Opcao invalida!

:end
echo.
pause
