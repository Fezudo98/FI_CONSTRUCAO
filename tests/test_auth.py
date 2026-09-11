def test_healthz(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_login_success(client, admin_user):
    resp = client.post("/api/auth/login", json={"email": admin_user["email"], "password": "senhaadmin123"})
    assert resp.status_code == 200
    assert resp.get_json()["user"]["email"] == admin_user["email"]


def test_login_wrong_password(client, admin_user):
    resp = client.post("/api/auth/login", json={"email": admin_user["email"], "password": "errada"})
    assert resp.status_code == 401


def test_me_requires_login(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 200
    assert resp.get_json()["user"] is None


def test_me_after_login(auth_client):
    resp = auth_client.get("/api/auth/me")
    assert resp.get_json()["user"]["email"] == "admin@teste.com"


def test_logout(auth_client):
    resp = auth_client.post("/api/auth/logout")
    assert resp.status_code == 200
    resp = auth_client.get("/api/auth/me")
    assert resp.get_json()["user"] is None


def test_protected_route_without_login(client):
    resp = client.get("/api/products")
    assert resp.status_code == 401
