@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Sistema nao instalado ainda. Rode instalar_sistema.bat primeiro.
  pause
  exit /b 1
)
.venv\Scripts\python.exe scripts\backup_database.py
if errorlevel 1 (
  echo.
  echo Backup FALHOU. Veja a mensagem acima.
) else (
  echo.
  echo Backup concluido.
)
pause
