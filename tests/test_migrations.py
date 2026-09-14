import os
import sqlite3
import subprocess
import sys


def test_fresh_database_upgrades_to_head(tmp_path):
    database = tmp_path / "fresh.db"
    env = os.environ.copy()
    env.update(
        DATABASE_URL=f"sqlite:///{database}",
        SECRET_KEY="migration-test-secret",
        FLASK_APP="run.py",
        FLASK_ENV="development",
    )

    result = subprocess.run(
        [sys.executable, "-m", "flask", "db", "upgrade"],
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    with sqlite3.connect(database) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(users)")}
        revision = connection.execute("SELECT version_num FROM alembic_version").fetchone()[0]
    assert "onboarding_completed_at" in columns
    assert revision == "20260914guide"


def test_existing_monodepot_database_receives_onboarding_column(tmp_path):
    database = tmp_path / "existing.db"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name VARCHAR(150) NOT NULL)")
        connection.execute("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)")
        connection.execute("INSERT INTO alembic_version VALUES ('20260912mono')")

    env = os.environ.copy()
    env.update(
        DATABASE_URL=f"sqlite:///{database}",
        SECRET_KEY="migration-test-secret",
        FLASK_APP="run.py",
        FLASK_ENV="development",
    )
    result = subprocess.run(
        [sys.executable, "-m", "flask", "db", "upgrade"],
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    with sqlite3.connect(database) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(users)")}
    assert "onboarding_completed_at" in columns
