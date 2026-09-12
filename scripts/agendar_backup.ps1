$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')

function Pause-ForUser([string]$Message) {
    Write-Host ''
    Write-Host $Message -ForegroundColor Yellow
    Read-Host 'Pressione Enter para fechar'
}

try {
    Write-Host '============================================' -ForegroundColor Cyan
    Write-Host ' F.I Construção - Agendar backup diario' -ForegroundColor Cyan
    Write-Host '============================================' -ForegroundColor Cyan

    $venvPython = Join-Path (Get-Location) '.venv\Scripts\python.exe'
    if (-not (Test-Path $venvPython)) { throw 'Sistema nao instalado. Execute instalar_sistema.bat primeiro.' }

    $scriptPath = Join-Path (Get-Location) 'scripts\backup_database.py'
    $workDir = (Get-Location).Path
    $taskName = 'FIConstrucao-BackupDiario'

    $time = Read-Host 'Horario diario do backup (HH:mm, padrao 22:00)'
    if ([string]::IsNullOrWhiteSpace($time)) { $time = '22:00' }

    $action = New-ScheduledTaskAction -Execute $venvPython -Argument "`"$scriptPath`"" -WorkingDirectory $workDir
    $trigger = New-ScheduledTaskTrigger -Daily -At $time
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings `
        -Description 'Backup diario do banco de dados do F.I Construcao (scripts/backup_database.py)' -Force | Out-Null

    Write-Host ''
    Write-Host "Tarefa '$taskName' agendada para rodar todo dia as $time." -ForegroundColor Green
    Write-Host 'Confira ou ajuste em: Agendador de Tarefas do Windows.'
    Write-Host 'Os arquivos de backup ficam em backups\ (mantidos por BACKUP_RETENTION_DAYS dias, padrao 14).'
} catch {
    Pause-ForUser ("ERRO: " + $_.Exception.Message + "`n`nSe o erro for de permissao, execute este script como Administrador.")
    exit 1
}

Pause-ForUser 'Agendamento concluido.'
