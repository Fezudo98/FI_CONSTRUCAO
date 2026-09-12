$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

function Pause-ForUser([string]$Message) {
    Write-Host ''
    Write-Host $Message -ForegroundColor Yellow
    Read-Host 'Pressione Enter para fechar'
}

function Get-PythonCommand {
    $launcher = Get-Command py -ErrorAction SilentlyContinue
    if ($launcher) { return @{ Path = $launcher.Source; Args = @('-3') } }
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) { return @{ Path = $python.Source; Args = @() } }
    throw 'Python 3.11 ou superior não foi encontrado. Instale-o e execute este instalador novamente.'
}

function Sync-Repository {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'Git não foi encontrado. Instale o Git for Windows e execute novamente.' }
    if (-not (Test-Path '.git')) { throw 'Esta pasta não é uma cópia do sistema Git. Clone o repositório antes de executar o instalador.' }
    $changes = git status --porcelain
    if ($changes) { throw 'Há alterações locais pendentes. Elas não foram sobrescritas; revise-as antes de atualizar.' }
    $branch = (git branch --show-current).Trim()
    if (-not $branch) { throw 'Não foi possível identificar a branch atual do sistema.' }
    Write-Host '[1/5] Buscando atualizações do sistema...'
    git fetch origin
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível buscar atualizações do repositório remoto.' }
    git pull --ff-only origin $branch
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível aplicar as atualizações do repositório remoto.' }
}

try {
    Write-Host '============================================' -ForegroundColor Cyan
    Write-Host ' F.I Construção - Instalação inicial' -ForegroundColor Cyan
    Write-Host '============================================' -ForegroundColor Cyan

    Sync-Repository
    $python = Get-PythonCommand
    $venvPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'

    if (-not (Test-Path $venvPython)) {
        Write-Host '[2/5] Criando ambiente do sistema...'
        & $python.Path @($python.Args) -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'Não foi possível criar o ambiente Python do sistema.' }
    } else {
        Write-Host '[2/5] Ambiente do sistema já existe.'
    }

    Write-Host '[3/5] Instalando dependências...'
    & $venvPython -m pip install --disable-pip-version-check --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível atualizar o instalador de dependências.' }
    & $venvPython -m pip install --disable-pip-version-check -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível instalar as dependências do sistema.' }

    if (-not (Test-Path '.env')) {
        Copy-Item '.env.example' '.env'
        Write-Host '[4/5] Arquivo .env criado.' -ForegroundColor Yellow
        Write-Host 'Configure o banco de dados, a chave SECRET_KEY e a senha do administrador.' -ForegroundColor Yellow
        Start-Process notepad.exe (Join-Path $PSScriptRoot '.env')
        Read-Host 'Salve o .env e pressione Enter para continuar'
    } else {
        Write-Host '[4/5] Configuração .env encontrada.'
    }

    Write-Host '[5/5] Criando/atualizando estrutura do banco...'
    & $venvPython scripts\bootstrap_database.py
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível preparar o banco de dados. Revise o arquivo .env.' }
    Write-Host ''
    Write-Host 'Instalação concluída. Execute iniciar_sistema.bat para usar o sistema.' -ForegroundColor Green
} catch {
    Pause-ForUser ("ERRO: " + $_.Exception.Message)
    exit 1
}

Pause-ForUser 'Instalador finalizado.'
