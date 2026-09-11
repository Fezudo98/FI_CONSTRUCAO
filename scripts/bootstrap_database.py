"""Cria as tabelas em um banco vazio e marca a revisão do Alembic como atual.
Uso: python scripts/bootstrap_database.py
Somente para instalação nova; para atualizar uma instalação existente use
`flask --app run.py db upgrade`."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from flask_migrate import stamp  # noqa: E402

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models.company import Company  # noqa: E402


def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        stamp()

        if Company.query.count() == 0:
            db.session.add(Company(name="Matriz", is_headquarters=True))
            db.session.commit()

        print("Banco inicial criado e marcado na revisão mais recente.")


if __name__ == "__main__":
    main()
