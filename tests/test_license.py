import json
from datetime import datetime, timezone

import requests

from scripts import check_license


def _configure(monkeypatch, tmp_path):
    monkeypatch.setenv("LICENSE_CHECK_URL", "https://license.invalid/check")
    monkeypatch.setenv("LICENSE_KEY", "test-key")
    monkeypatch.setattr(check_license, "CACHE_PATH", str(tmp_path / "license_cache.json"))


def test_invalid_server_response_does_not_use_active_cache(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path)
    with open(check_license.CACHE_PATH, "w", encoding="utf-8") as cache:
        json.dump({"status": "active", "checked_at": datetime.now(timezone.utc).isoformat()}, cache)

    class InvalidResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"unexpected": True}

    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: InvalidResponse())

    assert check_license.main() == 1


def test_network_failure_uses_recent_active_cache(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path)
    with open(check_license.CACHE_PATH, "w", encoding="utf-8") as cache:
        json.dump({"status": "active", "checked_at": datetime.now(timezone.utc).isoformat()}, cache)

    def fail(*args, **kwargs):
        raise requests.ConnectionError("offline")

    monkeypatch.setattr(requests, "get", fail)

    assert check_license.main() == 0
