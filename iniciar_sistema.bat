@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo   F.I Construcao - Iniciando sistema
echo ============================================

if not exist ".venv\Scripts\python.exe" (
    echo [setup] Ambiente virtual nao encontrado. Criando...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERRO] Nao foi possivel criar o ambiente virtual. Verifique se o Python esta instalado.
        pause
        exit /b 1
    )
    echo [setup] Instalando dependencias...
    ".venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
    ".venv\Scripts\python.exe" -m pip install --quiet -r requirements.txt
)

set PYTHON=.venv\Scripts\python.exe

if not exist ".env" (
    echo [ERRO] Arquivo .env nao encontrado. Copie .env.example para .env e configure antes de continuar.
    pause
    exit /b 1
)

echo.
echo [1/4] Verificando atualizacoes...
git pull --ff-only
if errorlevel 1 (
    echo [AVISO] Nao foi possivel atualizar via git ^(sem internet ou conflito local^). Continuando com a versao atual.
)

echo.
echo [2/4] Aplicando migracoes do banco de dados...
"%PYTHON%" -m flask db upgrade
if errorlevel 1 (
    echo [ERRO] Falha ao aplicar migracoes do banco de dados.
    pause
    exit /b 1
)

echo.
echo [3/4] Verificando licenca...
"%PYTHON%" scripts\check_license.py
if errorlevel 1 (
    echo.
    echo ============================================
    echo   ACESSO SUSPENSO
    echo   Entre em contato com o suporte para regularizar o acesso.
    echo ============================================
    pause
    exit /b 1
)

echo.
echo [4/4] Iniciando servidor...
start "" http://localhost:5000
"%PYTHON%" run.py

pause
