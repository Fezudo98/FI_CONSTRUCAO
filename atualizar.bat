@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo   F.I Construcao - Atualizando (sem iniciar)
echo ============================================

set PYTHON=.venv\Scripts\python.exe
if not exist "%PYTHON%" set PYTHON=python

echo.
echo Baixando atualizacoes do repositorio...
git pull --ff-only
if errorlevel 1 (
    echo [ERRO] Nao foi possivel atualizar. Verifique a conexao ou conflitos locais.
    pause
    exit /b 1
)

echo.
echo Instalando dependencias (se houver novas)...
"%PYTHON%" -m pip install --quiet -r requirements.txt

echo.
echo Aplicando migracoes do banco de dados...
"%PYTHON%" -m flask db upgrade

echo.
echo Atualizacao concluida. Use iniciar_sistema.bat para rodar o sistema.
pause
