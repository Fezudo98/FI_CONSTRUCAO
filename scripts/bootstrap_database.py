"""Cria as tabelas e marca a revisão do Alembic como atual.
Uso inicial: python scripts/bootstrap_database.py --reset
Somente para instalação nova; para atualizar uma instalação existente use
`flask --app run.py db upgrade`."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from flask_migrate import stamp  # noqa: E402
from sqlalchemy import MetaData  # noqa: E402

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
def main():
    reset = "--reset" in sys.argv
    if reset and "--confirm-reset=APAGAR" not in sys.argv:
        print("Reset recusado. Informe --confirm-reset=APAGAR para recriar o banco.")
        sys.exit(2)
    app = create_app()
    with app.app_context():
        if reset:
            existing_schema = MetaData()
            existing_schema.reflect(bind=db.engine)
            existing_schema.drop_all(bind=db.engine)
        db.create_all()
        stamp()
        print("Banco monodepósito criado e marcado na revisão mais recente.")


if __name__ == "__main__":
    main()
