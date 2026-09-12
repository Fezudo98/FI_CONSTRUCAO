import os

import pytest

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("FLASK_ENV", "development")


@pytest.fixture()
def app(tmp_path):
    # Usa um arquivo dentro de um TemporaryDirectory (pytest tmp_path) em vez de
    # tempfile.mkstemp: no Windows, manter o descritor de mkstemp aberto ao
    # mesmo tempo que o SQLite abre o mesmo arquivo causa PermissionError ao
    # tentar apagar o banco no teardown.
    db_path = tmp_path / "test.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

    from app import create_app
    from app.extensions import db

    flask_app = create_app()
    flask_app.config.update(TESTING=True)

    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def admin_user(app):
    from app.extensions import db
    from app.models.user import User, ROLE_ADMIN
    from app.services.auth import hash_password

    with app.app_context():
        user = User(
            name="Admin",
            email="admin@teste.com",
            password_hash=hash_password("senhaadmin123"),
            role=ROLE_ADMIN,
        )
        db.session.add(user)
        db.session.commit()
        return {"id": user.id, "email": user.email}


@pytest.fixture()
def auth_client(client, admin_user):
    resp = client.post("/api/auth/login", json={"email": admin_user["email"], "password": "senhaadmin123"})
    assert resp.status_code == 200
    return client
