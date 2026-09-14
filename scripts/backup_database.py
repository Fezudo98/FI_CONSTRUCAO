"""Backup do banco de dados de producao (PostgreSQL) do deposito.
Gera um arquivo .dump (formato custom do pg_dump, restauravel com pg_restore)
em backups/, e apaga backups mais antigos que BACKUP_RETENTION_DAYS.

Uso: python scripts/backup_database.py
Agendamento: scripts/agendar_backup.ps1 registra isso como tarefa diaria do
Windows (Agendador de Tarefas).
"""
import glob
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKUPS_DIR = os.path.join(PROJECT_DIR, "backups")
RETENTION_DAYS = int(os.environ.get("BACKUP_RETENTION_DAYS", "14"))


def _find_pg_dump():
    configured = os.environ.get("PG_DUMP_PATH", "").strip()
    if configured and os.path.isfile(configured):
        return configured

    available = shutil.which("pg_dump")
    if available:
        return available

    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    candidates = glob.glob(os.path.join(program_files, "PostgreSQL", "*", "bin", "pg_dump.exe"))
    if candidates:
        def version(path):
            directory = os.path.basename(os.path.dirname(os.path.dirname(path)))
            try:
                return tuple(int(part) for part in directory.split("."))
            except ValueError:
                return (0,)

        return max(candidates, key=version)
    return configured or "pg_dump"


def _parse_database_url(url: str):
    parsed = urlparse(url)
    if not parsed.scheme.startswith("postgresql"):
        return None
    return {
        "host": parsed.hostname or "localhost",
        "port": str(parsed.port or 5432),
        "user": parsed.username or "",
        "password": parsed.password or "",
        "dbname": parsed.path.lstrip("/"),
    }


def _prune_old_backups():
    if not os.path.isdir(BACKUPS_DIR):
        return
    cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)
    for name in os.listdir(BACKUPS_DIR):
        path = os.path.join(BACKUPS_DIR, name)
        if not name.startswith("fi_construcao_") or not name.endswith(".dump"):
            continue
        if datetime.fromtimestamp(os.path.getmtime(path)) < cutoff:
            os.remove(path)
            print(f"[backup] Removido backup antigo: {name}")


def main() -> int:
    database_url = os.environ.get("DATABASE_URL", "")
    conn = _parse_database_url(database_url)
    if conn is None:
        print(
            "[backup] DATABASE_URL nao e PostgreSQL (uso local em SQLite nao precisa "
            "de backup via pg_dump). Nada a fazer."
        )
        return 0

    if not conn["dbname"] or not conn["user"]:
        print("[backup] DATABASE_URL incompleta (faltam usuario ou nome do banco).")
        return 1

    os.makedirs(BACKUPS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(BACKUPS_DIR, f"fi_construcao_{timestamp}.dump")

    pg_dump = _find_pg_dump()
    env = os.environ.copy()
    if conn["password"]:
        env["PGPASSWORD"] = conn["password"]

    cmd = [
        pg_dump,
        "-h", conn["host"],
        "-p", conn["port"],
        "-U", conn["user"],
        "-Fc",
        "-f", dest,
        conn["dbname"],
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600, env=env)
    except FileNotFoundError:
        print(
            f"[backup] pg_dump nao encontrado ('{pg_dump}'). Instale as ferramentas de linha "
            "de comando do PostgreSQL ou configure PG_DUMP_PATH no .env apontando para "
            "o pg_dump.exe (ex.: C:\\Program Files\\PostgreSQL\\16\\bin\\pg_dump.exe)."
        )
        return 1
    except subprocess.TimeoutExpired:
        print("[backup] Tempo limite excedido rodando pg_dump.")
        return 1

    if result.returncode != 0:
        print(f"[backup] Falha no pg_dump: {result.stderr.strip()}")
        if os.path.isfile(dest):
            os.remove(dest)
        return 1

    size_mb = os.path.getsize(dest) / (1024 * 1024)
    print(f"[backup] Backup criado: {dest} ({size_mb:.2f} MB)")

    _prune_old_backups()
    return 0


if __name__ == "__main__":
    sys.exit(main())
