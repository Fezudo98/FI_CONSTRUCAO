"""Restaura um backup gerado por scripts/backup_database.py.
ATENCAO: apaga os dados atuais do banco e substitui pelo conteudo do backup.

Uso: python scripts/restore_database.py backups/fi_construcao_20260101_220000.dump
"""
import os
import subprocess
import sys
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()


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


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: python scripts/restore_database.py <arquivo.dump>")
        return 1

    backup_path = sys.argv[1]
    if not os.path.isfile(backup_path):
        print(f"[restore] Arquivo nao encontrado: {backup_path}")
        return 1

    conn = _parse_database_url(os.environ.get("DATABASE_URL", ""))
    if conn is None:
        print("[restore] DATABASE_URL nao e PostgreSQL. Restauracao via pg_restore nao se aplica.")
        return 1

    print(f"ATENCAO: isso vai APAGAR os dados atuais de '{conn['dbname']}' em {conn['host']}")
    print(f"e substituir pelo conteudo de: {backup_path}")
    confirm = input("Digite RESTAURAR para confirmar: ")
    if confirm != "RESTAURAR":
        print("[restore] Cancelado.")
        return 1

    pg_restore = os.environ.get("PG_RESTORE_PATH", "").strip() or "pg_restore"
    env = os.environ.copy()
    if conn["password"]:
        env["PGPASSWORD"] = conn["password"]

    cmd = [
        pg_restore,
        "-h", conn["host"],
        "-p", conn["port"],
        "-U", conn["user"],
        "-d", conn["dbname"],
        "--clean", "--if-exists",
        backup_path,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=900, env=env)
    except FileNotFoundError:
        print(
            f"[restore] pg_restore nao encontrado ('{pg_restore}'). Configure PG_RESTORE_PATH "
            "no .env apontando para o pg_restore.exe (mesma pasta do pg_dump.exe)."
        )
        return 1
    except subprocess.TimeoutExpired:
        print("[restore] Tempo limite excedido rodando pg_restore.")
        return 1

    if result.returncode != 0:
        print(f"[restore] pg_restore terminou com avisos/erros:\n{result.stderr.strip()}")
        print("[restore] Confira se os dados foram restaurados corretamente antes de usar o sistema.")
        return 1

    print("[restore] Banco restaurado com sucesso.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
