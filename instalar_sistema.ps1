param(
    [switch]$Elevated,
    [string]$InstallUserSid = ''
)

$ErrorActionPreference = 'Stop'
$RepositoryUrl = 'https://github.com/Fezudo98/FI_CONSTRUCAO.git'
$InstallDir = Join-Path $env:ProgramData 'FIConstrucao'
$DatabaseName = 'fi_construcao'
$DatabaseUser = 'fi_construcao'
$LicenseUrl = 'https://vps69719.publiccloud.com.br/puma/servidores/api/licenses/check'

function Pause-ForUser([string]$Message) {
    Write-Host ''; Write-Host $Message -ForegroundColor Yellow
    Read-Host 'Pressione Enter para fechar'
}

function Test-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Restart-Elevated {
    $sid = if ($InstallUserSid) { $InstallUserSid } else { [Security.Principal.WindowsIdentity]::GetCurrent().User.Value }
    $arguments = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', ('"{0}"' -f $PSCommandPath), '-Elevated', '-InstallUserSid', $sid)
    Start-Process powershell.exe -Verb RunAs -ArgumentList $arguments -WorkingDirectory $PSScriptRoot
}

function Refresh-Path {
    $machinePath = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = "$machinePath;$userPath"
}

function Install-Package([string]$Id, [string]$Name, [string[]]$Extra = @()) {
    Write-Host "Instalando $Name..." -ForegroundColor Cyan
    $arguments = @('install', '--id', $Id, '--exact', '--source', 'winget', '--accept-package-agreements', '--accept-source-agreements', '--silent', '--disable-interactivity') + $Extra
    & $script:Winget @arguments
    if ($LASTEXITCODE -ne 0) { throw "Não foi possível instalar $Name pelo winget." }
    Refresh-Path
}

function Find-Python {
    $commands = @()
    $py = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($py) { $commands += ,@($py.Source, '-3.12') }
    $python = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($python -and $python.Source -notmatch 'WindowsApps') { $commands += ,@($python.Source) }
    foreach ($candidate in $commands) {
        try {
            $prefix = @($candidate | Select-Object -Skip 1)
            $valid = & $candidate[0] @prefix -c 'import sys; print(int(sys.version_info >= (3, 11)))' 2>$null
            if ($LASTEXITCODE -eq 0 -and $valid -eq '1') { return @{ Path = $candidate[0]; Args = $prefix } }
        } catch { }
    }
    $null
}

function Ensure-Prerequisites {
    $winget = Get-Command winget.exe -ErrorAction SilentlyContinue
    if (-not $winget) { throw 'Instale ou atualize "Instalador de Aplicativo" pela Microsoft Store para disponibilizar o winget.' }
    $script:Winget = $winget.Source
    if (-not (Get-Command git.exe -ErrorAction SilentlyContinue)) { Install-Package 'Git.Git' 'Git for Windows' }
    if (-not (Find-Python)) { Install-Package 'Python.Python.3.12' 'Python 3.12' @('--scope', 'machine') }
    $script:Python = Find-Python
    if (-not $script:Python) { throw 'Python 3.11 ou superior não foi localizado após a instalação.' }
}

function Sync-Repository {
    if (-not (Test-Path (Join-Path $PSScriptRoot '.git'))) {
        if (-not (Test-Path (Join-Path $InstallDir '.git'))) {
            Write-Host "Clonando o sistema em $InstallDir..." -ForegroundColor Cyan
            & git clone $RepositoryUrl $InstallDir
            if ($LASTEXITCODE -ne 0) { throw 'Não foi possível clonar o sistema do GitHub.' }
        }
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $InstallDir 'instalar_sistema.ps1') -Elevated -InstallUserSid $InstallUserSid
        if ($LASTEXITCODE -ne 0) { throw 'A instalação na pasta definitiva não foi concluída.' }
        exit 0
    }
    Set-Location $PSScriptRoot
    if (git status --porcelain) { throw 'Há alterações locais pendentes. A atualização foi interrompida para preservar os arquivos.' }
    $branch = (git branch --show-current).Trim()
    if (-not $branch) { throw 'Não foi possível identificar a branch atual.' }
    Write-Host '[1/9] Buscando atualizações...'
    & git fetch origin
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível consultar o GitHub.' }
    & git pull --ff-only origin $branch
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível aplicar as atualizações.' }
}

function New-Secret([int]$Bytes = 32) {
    $buffer = New-Object byte[] $Bytes
    [Security.Cryptography.RandomNumberGenerator]::Fill($buffer)
    [Convert]::ToBase64String($buffer).Replace('+', 'A').Replace('/', 'B').TrimEnd('=')
}

function ConvertTo-PlainText([Security.SecureString]$Value) {
    $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($Value)
    try { [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer) }
}

function Get-EnvValue([string]$Name) {
    if (-not (Test-Path '.env')) { return '' }
    $line = Get-Content '.env' | Where-Object { $_ -match "^$([regex]::Escape($Name))=" } | Select-Object -Last 1
    if ($line) { return ($line -split '=', 2)[1].Trim() }
    ''
}

function Set-EnvValue([string]$Name, [string]$Value) {
    $lines = if (Test-Path '.env') { [Collections.Generic.List[string]](Get-Content '.env') } else { [Collections.Generic.List[string]]::new() }
    $found = $false
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match "^$([regex]::Escape($Name))=") { $lines[$i] = "$Name=$Value"; $found = $true }
    }
    if (-not $found) { $lines.Add("$Name=$Value") }
    [IO.File]::WriteAllLines((Join-Path $PSScriptRoot '.env'), $lines, [Text.UTF8Encoding]::new($false))
}

function Configure-Environment {
    $fresh = -not (Test-Path '.env')
    if ($fresh) { Copy-Item '.env.example' '.env' }
    $secret = Get-EnvValue 'SECRET_KEY'
    if (-not $secret -or $secret -eq 'troque-por-uma-chave-aleatoria-longa') { Set-EnvValue 'SECRET_KEY' (New-Secret 48) }
    Set-EnvValue 'APP_TIMEZONE' 'America/Fortaleza'
    $licenseKey = Get-EnvValue 'LICENSE_KEY'
    while (-not $licenseKey) {
        $licenseKey = (Read-Host 'Chave de licença fornecida pelo suporte').Trim()
        if (-not $licenseKey) { Write-Host 'A chave de licença é obrigatória.' -ForegroundColor Yellow }
    }
    Set-EnvValue 'LICENSE_KEY' $licenseKey
    if (-not (Get-EnvValue 'LICENSE_CHECK_URL')) { Set-EnvValue 'LICENSE_CHECK_URL' $LicenseUrl }
    $fresh
}

function Find-PostgresTool([string]$Name) {
    $command = Get-Command "$Name.exe" -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    Get-ChildItem "$env:ProgramFiles\PostgreSQL\*\bin\$Name.exe" -ErrorAction SilentlyContinue |
        Sort-Object { [version]$_.Directory.Parent.Name } -Descending |
        Select-Object -First 1 -ExpandProperty FullName
}

function Ensure-PostgreSQL {
    $psql = Find-PostgresTool 'psql'
    $installedNow = $false
    if (-not $psql) {
        $postgresPassword = New-Secret 24
        $installed = $false
        foreach ($id in @('PostgreSQL.PostgreSQL.17', 'PostgreSQL.PostgreSQL.16')) {
            $override = "--mode unattended --unattendedmodeui none --superpassword $postgresPassword --serverport 5432"
            & $script:Winget install --id $id --exact --source winget --accept-package-agreements --accept-source-agreements --silent --disable-interactivity --override $override
            if ($LASTEXITCODE -eq 0) { $installed = $true; break }
        }
        if (-not $installed) { throw 'Não foi possível instalar o PostgreSQL automaticamente.' }
        Refresh-Path
        $psql = Find-PostgresTool 'psql'
        $installedNow = $true
    }
    if (-not $psql) { throw 'O utilitário psql não foi localizado.' }
    $pgDump = Find-PostgresTool 'pg_dump'
    $pgRestore = Find-PostgresTool 'pg_restore'
    if (-not $pgDump -or -not $pgRestore) { throw 'As ferramentas de backup do PostgreSQL não foram localizadas.' }
    Set-EnvValue 'PG_DUMP_PATH' $pgDump
    Set-EnvValue 'PG_RESTORE_PATH' $pgRestore
    $postgresService = Get-Service -Name 'postgresql*' -ErrorAction SilentlyContinue |
        Sort-Object Name -Descending | Select-Object -First 1
    if ($postgresService -and $postgresService.Status -ne 'Running') {
        Start-Service $postgresService.Name
        $postgresService.WaitForStatus('Running', (New-TimeSpan -Seconds 30))
    }
    if (-not $installedNow) {
        Write-Host 'PostgreSQL já instalado. Informe a senha administrativa.' -ForegroundColor Yellow
        $postgresPassword = ConvertTo-PlainText (Read-Host 'Senha do usuário postgres' -AsSecureString)
    }

    $appPassword = Get-EnvValue 'FI_DATABASE_PASSWORD'
    if (-not $appPassword) { $appPassword = New-Secret 24 }
    $env:PGPASSWORD = $postgresPassword
    try {
        $probe = & $psql -h localhost -p 5432 -U postgres -d postgres -tAc 'SELECT 1' 2>&1
        if ($LASTEXITCODE -ne 0) { throw "Não foi possível acessar o PostgreSQL: $probe" }
        $roleExists = (& $psql -h localhost -p 5432 -U postgres -d postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DatabaseUser'").Trim()
        $roleSql = if ($roleExists -eq '1') { "ALTER ROLE $DatabaseUser WITH LOGIN PASSWORD '$appPassword'" } else { "CREATE ROLE $DatabaseUser WITH LOGIN PASSWORD '$appPassword'" }
        & $psql -h localhost -p 5432 -U postgres -d postgres -v ON_ERROR_STOP=1 -c $roleSql | Out-Null
        if ($LASTEXITCODE -ne 0) { throw 'Não foi possível preparar o usuário do banco.' }
        $databaseExists = (& $psql -h localhost -p 5432 -U postgres -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$DatabaseName'").Trim()
        if ($databaseExists -ne '1') {
            & $psql -h localhost -p 5432 -U postgres -d postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE $DatabaseName OWNER $DatabaseUser" | Out-Null
            if ($LASTEXITCODE -ne 0) { throw 'Não foi possível criar o banco de dados.' }
        }
    } finally { Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue }
    Set-EnvValue 'FI_DATABASE_PASSWORD' $appPassword
    Set-EnvValue 'DATABASE_URL' "postgresql+psycopg2://${DatabaseUser}:$([Uri]::EscapeDataString($appPassword))@localhost:5432/$DatabaseName"
}

function Ensure-Administrator([string]$PythonPath) {
    $count = & $PythonPath -c "from app import create_app; from app.models.user import User; a=create_app(); c=a.app_context(); c.push(); print(User.query.count()); c.pop()"
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível consultar os usuários.' }
    if ([int]$count -gt 0) { Write-Host 'Usuário existente preservado.'; return }
    do {
        $password = ConvertTo-PlainText (Read-Host 'Crie a senha do administrador (mínimo 10 caracteres)' -AsSecureString)
    } while ($password.Length -lt 10)
    if (-not (Get-EnvValue 'DEV_ADMIN_EMAIL')) { Set-EnvValue 'DEV_ADMIN_EMAIL' 'admin@ficonstrucao.com.br' }
    Set-EnvValue 'DEV_ADMIN_PASSWORD' $password
    & $PythonPath create_dev_admin.py
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível criar o administrador.' }
    Set-EnvValue 'DEV_ADMIN_PASSWORD' ''
}

function Configure-OperatingSystem([string]$PythonPath) {
    $sid = if ($InstallUserSid) { $InstallUserSid } else { [Security.Principal.WindowsIdentity]::GetCurrent().User.Value }
    $permission = "*${sid}:(OI)(CI)M"
    & icacls.exe $PSScriptRoot /grant:r $permission /T /C /Q | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível liberar a pasta do sistema para atualizações diárias.' }

    $rule = 'F.I Construção - PDV porta 5000'
    if (-not (Get-NetFirewallRule -DisplayName $rule -ErrorAction SilentlyContinue)) {
        New-NetFirewallRule -DisplayName $rule -Direction Inbound -Action Allow -Protocol TCP -LocalPort 5000 -Profile Private | Out-Null
    }
    $action = New-ScheduledTaskAction -Execute $PythonPath -Argument ('"{0}"' -f (Join-Path $PSScriptRoot 'scripts\backup_database.py')) -WorkingDirectory $PSScriptRoot
    $trigger = New-ScheduledTaskTrigger -Daily -At '22:00'
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd -ExecutionTimeLimit (New-TimeSpan -Minutes 30)
    Register-ScheduledTask -TaskName 'FIConstrucao-BackupDiario' -Action $action -Trigger $trigger -Settings $settings -Description 'Backup diário do banco F.I Construção' -Force | Out-Null

    $desktop = [Environment]::GetFolderPath('CommonDesktopDirectory')
    $shell = New-Object -ComObject WScript.Shell
    foreach ($item in @(
        @{ Name = 'F.I Construção.lnk'; Target = (Join-Path $PSScriptRoot 'iniciar_sistema.bat') },
        @{ Name = 'Atualizar F.I Construção.lnk'; Target = (Join-Path $PSScriptRoot 'instalar_sistema.bat') }
    )) {
        $shortcut = $shell.CreateShortcut((Join-Path $desktop $item.Name))
        $shortcut.TargetPath = $item.Target; $shortcut.WorkingDirectory = $PSScriptRoot; $shortcut.Save()
    }
}

try {
    Write-Host '================================================' -ForegroundColor Cyan
    Write-Host ' F.I Construção - Instalação completa' -ForegroundColor Cyan
    Write-Host '================================================' -ForegroundColor Cyan
    if (-not (Test-Administrator)) { Restart-Elevated; exit 0 }
    if (-not $InstallUserSid) { $InstallUserSid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value }

    Ensure-Prerequisites
    Sync-Repository
    Set-Location $PSScriptRoot
    Write-Host '[2/9] Preparando ambiente Python...'
    $venvPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path $venvPython)) {
        & $script:Python.Path @($script:Python.Args) -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'Não foi possível criar o ambiente Python.' }
    }
    & $venvPython -m pip install --disable-pip-version-check --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível atualizar o pip.' }
    & $venvPython -m pip install --disable-pip-version-check -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível instalar as dependências.' }

    Write-Host '[3/9] Configurando o sistema...'; $fresh = Configure-Environment
    Write-Host '[4/9] Preparando PostgreSQL...'; Ensure-PostgreSQL
    if (-not $fresh) {
        Write-Host '[5/9] Criando backup de segurança...'; & $venvPython scripts\backup_database.py
        if ($LASTEXITCODE -ne 0) { throw 'O backup falhou; a atualização foi cancelada.' }
    } else { Write-Host '[5/9] Instalação nova; não há banco anterior para copiar.' }
    Write-Host '[6/9] Aplicando banco...'; & $venvPython -m flask db upgrade
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível aplicar as migrações.' }
    Write-Host '[7/9] Configurando administrador...'; Ensure-Administrator $venvPython
    Write-Host '[8/9] Configurando rede, atalhos e backup...'; Configure-OperatingSystem $venvPython
    Write-Host '[9/9] Verificando licença...'; & $venvPython scripts\check_license.py
    if ($LASTEXITCODE -ne 0) { throw 'A instalação terminou, mas a licença não foi validada.' }
    Write-Host ''; Write-Host 'Instalação concluída. O sistema será iniciado em uma nova janela.' -ForegroundColor Green
    Start-Process (Join-Path $PSScriptRoot 'iniciar_sistema.bat') -WorkingDirectory $PSScriptRoot
} catch {
    Pause-ForUser ("ERRO: " + $_.Exception.Message); exit 1
}

Pause-ForUser 'Instalador finalizado.'
