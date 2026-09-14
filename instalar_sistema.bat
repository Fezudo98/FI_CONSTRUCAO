@echo off
setlocal
title F.I Construcao - Instalador

set "INSTALLER_PS1=%~dp0instalar_sistema.ps1"

if not exist "%INSTALLER_PS1%" (
    echo Baixando o instalador oficial do F.I Construcao...
    set "INSTALLER_PS1=%TEMP%\FIConstrucaoInstaller\instalar_sistema.ps1"
    if not exist "%TEMP%\FIConstrucaoInstaller" mkdir "%TEMP%\FIConstrucaoInstaller"

    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
        "$ErrorActionPreference='Stop'; Invoke-WebRequest -UseBasicParsing -Uri 'https://raw.githubusercontent.com/Fezudo98/FI_CONSTRUCAO/main/instalar_sistema.ps1' -OutFile '%TEMP%\FIConstrucaoInstaller\instalar_sistema.ps1'"

    if errorlevel 1 (
        echo.
        echo ERRO: Nao foi possivel baixar o instalador. Verifique a internet e tente novamente.
        pause
        exit /b 1
    )
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%INSTALLER_PS1%"
set "RESULT=%ERRORLEVEL%"

if not "%RESULT%"=="0" (
    echo.
    echo A instalacao nao foi concluida.
    pause
)

exit /b %RESULT%
