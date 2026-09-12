"""Cria o primeiro usuário administrador a partir das variáveis DEV_ADMIN_*.
Uso: python create_dev_admin.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

load_dotenv()

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models.user import User, ROLE_ADMIN  # noqa: E402
from app.services.auth import hash_password  # noqa: E402


def main():
    email = os.environ.get("DEV_ADMIN_EMAIL", "").strip().lower()
    password = os.environ.get("DEV_ADMIN_PASSWORD", "")
    name = os.environ.get("DEV_ADMIN_NAME", "Administrador")

    if not email or not password:
        print("Defina DEV_ADMIN_EMAIL e DEV_ADMIN_PASSWORD no .env antes de rodar este script.")
        sys.exit(1)
    if len(password) < 10:
        print("DEV_ADMIN_PASSWORD precisa ter no mínimo 10 caracteres.")
        sys.exit(1)

    app = create_app()
    with app.app_context():
        if User.query.filter_by(email=email).first() is not None:
            print(f"Já existe um usuário com o e-mail {email}.")
            return

        user = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            role=ROLE_ADMIN,
        )
        db.session.add(user)
        db.session.commit()
        print("Admin criado com sucesso!")


if __name__ == "__main__":
    main()
