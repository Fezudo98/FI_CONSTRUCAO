$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

function Pause-ForUser([string]$Message) {
    Write-Host ''
    Write-Host $Message -ForegroundColor Yellow
    Read-Host 'Pressione Enter para fechar'
}

function Sync-Repository {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'Git não foi encontrado. Execute o instalador novamente após instalar o Git for Windows.' }
    $changes = git status --porcelain
    if ($changes) { throw 'Há alterações locais pendentes. O sistema não foi atualizado para evitar sobrescrever arquivos.' }
    $branch = (git branch --show-current).Trim()
    if (-not $branch) { throw 'Não foi possível identificar a branch atual do sistema.' }
    Write-Host '[1/4] Buscando e aplicando atualizações...'
    git fetch origin
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível buscar atualizações do repositório remoto.' }
    git pull --ff-only origin $branch
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível aplicar as atualizações do repositório remoto.' }
}

try {
    Write-Host '============================================' -ForegroundColor Cyan
    Write-Host ' F.I Construção - Iniciando sistema' -ForegroundColor Cyan
    Write-Host '============================================' -ForegroundColor Cyan

    if (-not (Test-Path '.venv\Scripts\python.exe')) { throw 'Sistema não instalado. Execute instalar_sistema.bat primeiro.' }
    if (-not (Test-Path '.env')) { throw 'Arquivo .env não encontrado. Execute instalar_sistema.bat para configurar esta máquina.' }
    $envContent = Get-Content -Raw '.env'
    if ($envContent -match 'SECRET_KEY=troque-por-uma-chave-aleatoria-longa') {
        throw 'Configure uma SECRET_KEY exclusiva no arquivo .env antes de iniciar.'
    }

    Sync-Repository
    $venvPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
    Write-Host '[2/4] Verificando dependências...'
    & $venvPython -m pip install --disable-pip-version-check -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível instalar as dependências novas.' }

    Write-Host '[3/4] Aplicando atualizações do banco...'
    & $venvPython -m flask db upgrade
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível aplicar as atualizações do banco.' }

    Write-Host '[4/4] Verificando licença...'
    & $venvPython scripts\check_license.py
    if ($LASTEXITCODE -ne 0) { throw 'Licença indisponível ou suspensa. O sistema não será iniciado.' }

    Write-Host ''
    Write-Host 'Sistema disponível em http://localhost:5000' -ForegroundColor Green
    Write-Host 'Para outros dispositivos, use o IP deste computador seguido de :5000.' -ForegroundColor Green
    Start-Process 'http://localhost:5000'
    & $venvPython run.py
} catch {
    Pause-ForUser ("ERRO: " + $_.Exception.Message)
    exit 1
}

Pause-ForUser 'Sistema encerrado.'
