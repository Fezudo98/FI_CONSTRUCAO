param([switch]$Elevated)

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

function Pause-ForUser([string]$Message) {
    Write-Host ''
    Write-Host $Message -ForegroundColor Yellow
    Read-Host 'Pressione Enter para fechar'
}

function Get-LanAddress {
    try {
        $route = Get-NetRoute -DestinationPrefix '0.0.0.0/0' -ErrorAction Stop |
            Where-Object { $_.NextHop -ne '0.0.0.0' } |
            Sort-Object RouteMetric, InterfaceMetric |
            Select-Object -First 1
        if ($route) {
            $address = Get-NetIPAddress -AddressFamily IPv4 -InterfaceIndex $route.InterfaceIndex -ErrorAction Stop |
                Where-Object { $_.IPAddress -notlike '169.254.*' -and $_.IPAddress -ne '127.0.0.1' } |
                Select-Object -First 1 -ExpandProperty IPAddress
            if ($address) { return $address }
        }
    } catch { }

    try {
        $matches = [regex]::Matches((& ipconfig.exe | Out-String), '(?im)IPv4[^:]*:\s*(\d{1,3}(?:\.\d{1,3}){3})')
        $addresses = @($matches | ForEach-Object { $_.Groups[1].Value } |
            Where-Object { $_ -ne '127.0.0.1' -and $_ -notlike '169.254.*' })
        $private = $addresses | Where-Object {
            $_ -like '10.*' -or $_ -like '192.168.*' -or
            ($_ -match '^172\.(1[6-9]|2\d|3[01])\.')
        } | Select-Object -First 1
        if ($private) { return $private }
        if ($addresses.Count -gt 0) { return $addresses[0] }
    } catch { }
    return $null
}

function Get-SystemPort([string]$EnvContent) {
    $match = [regex]::Match($EnvContent, '(?m)^PORT=(\d+)\s*$')
    if ($match.Success) { return [int]$match.Groups[1].Value }
    return 5000
}

function Sync-Repository {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'Git não foi encontrado. Execute o instalador novamente após instalar o Git for Windows.' }
    $changes = git status --porcelain
    if ($changes) { throw 'Há alterações locais pendentes. O sistema não foi atualizado para evitar sobrescrever arquivos.' }
    $branch = (git branch --show-current).Trim()
    if (-not $branch) { throw 'Não foi possível identificar a branch atual do sistema.' }
    Write-Host '[1/5] Buscando e aplicando atualizações...'
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
    Write-Host '[2/5] Verificando dependências...'
    & $venvPython -m pip install --disable-pip-version-check -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível instalar as dependências novas.' }

    Write-Host '[3/5] Criando backup antes de atualizar o banco...'
    & $venvPython scripts\backup_database.py
    if ($LASTEXITCODE -ne 0) { throw 'O backup falhou; a atualização do banco foi cancelada por segurança.' }

    Write-Host '[4/5] Aplicando atualizações do banco...'
    & $venvPython -m flask db upgrade
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível aplicar as atualizações do banco.' }

    Write-Host '[5/5] Verificando licença...'
    & $venvPython scripts\check_license.py
    if ($LASTEXITCODE -ne 0) { throw 'Licença indisponível ou suspensa. O sistema não será iniciado.' }

    $port = Get-SystemPort $envContent
    $localUrl = "http://localhost:$port"
    $lanAddress = Get-LanAddress
    Write-Host ''
    Write-Host "Sistema local: $localUrl" -ForegroundColor Green
    if ($lanAddress) {
        Write-Host "Celular e outros dispositivos: http://${lanAddress}:$port" -ForegroundColor Green
    } else {
        Write-Host 'Não foi possível identificar o IP da rede. Verifique se o computador está conectado ao Wi-Fi ou cabo.' -ForegroundColor Yellow
    }

    $server = Start-Process $venvPython -ArgumentList 'run.py' -WorkingDirectory $PSScriptRoot -NoNewWindow -PassThru
    $ready = $false
    for ($attempt = 1; $attempt -le 30; $attempt++) {
        if ($server.HasExited) { throw "O servidor encerrou durante a inicialização (código $($server.ExitCode))." }
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri $localUrl -TimeoutSec 2
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) { $ready = $true; break }
        } catch { }
        Start-Sleep -Seconds 1
    }
    if (-not $ready) {
        Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue
        throw 'O servidor não respondeu em até 30 segundos.'
    }
    Start-Process $localUrl
    Write-Host 'Navegador aberto. Mantenha esta janela aberta enquanto estiver usando o sistema.' -ForegroundColor Cyan
    Wait-Process -Id $server.Id
    if ($server.ExitCode -ne 0) { throw "O servidor foi encerrado com código $($server.ExitCode)." }
} catch {
    Pause-ForUser ("ERRO: " + $_.Exception.Message)
    exit 1
}

Pause-ForUser 'Sistema encerrado.'
