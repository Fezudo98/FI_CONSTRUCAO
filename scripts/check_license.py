"""Verifica com a VPS se a licença deste depósito está em dia antes de iniciar
o sistema. Usa um cache local (license_cache.json) para tolerar quedas de
internet por até LICENSE_GRACE_DAYS dias.

Códigos de saída:
  0 = pode iniciar o sistema
  1 = bloqueado (licença suspensa ou cache expirado sem internet)

LICENSE_CHECK_URL e LICENSE_KEY são obrigatórios na instalação do cliente.
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

CACHE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "license_cache.json")
GRACE_DAYS = int(os.environ.get("LICENSE_GRACE_DAYS", "7"))


def _read_cache():
    if not os.path.isfile(CACHE_PATH):
        return None
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return None


def _write_cache(status: str):
    with open(CACHE_PATH, "w", encoding="utf-8") as fh:
        json.dump({"status": status, "checked_at": datetime.now(timezone.utc).isoformat()}, fh)


def main() -> int:
    check_url = os.environ.get("LICENSE_CHECK_URL", "").strip()
    license_key = os.environ.get("LICENSE_KEY", "").strip()

    if not check_url or not license_key:
        print("[licenca] LICENSE_CHECK_URL/LICENSE_KEY nao configurados. Bloqueando inicializacao.")
        return 1

    import requests

    try:
        resp = requests.get(check_url, params={"key": license_key}, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        status = data.get("status", "active")
    except Exception as exc:  # rede indisponível, VPS fora do ar, etc.
        print(f"[licenca] Nao foi possivel contatar o servidor de licenca: {exc}")
        cache = _read_cache()
        if cache is None:
            print("[licenca] Sem verificacao anterior em cache. Bloqueando por seguranca.")
            return 1

        checked_at = datetime.fromisoformat(cache["checked_at"])
        if datetime.now(timezone.utc) - checked_at > timedelta(days=GRACE_DAYS):
            print(f"[licenca] Cache expirado (mais de {GRACE_DAYS} dias sem contato). Bloqueando.")
            return 1

        if cache["status"] != "active":
            print("[licenca] Ultimo status conhecido era suspenso. Bloqueando.")
            return 1

        print(f"[licenca] Usando cache valido de {cache['checked_at']} (modo offline).")
        return 0

    _write_cache(status)

    if status != "active":
        print(f"[licenca] Acesso suspenso. Entre em contato com o suporte. (status={status})")
        return 1

    print("[licenca] Licenca ativa.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
