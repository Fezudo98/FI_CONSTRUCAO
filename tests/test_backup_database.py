from scripts import backup_database


def test_find_pg_dump_in_postgresql_installation(monkeypatch, tmp_path):
    executable = tmp_path / "PostgreSQL" / "17" / "bin" / "pg_dump.exe"
    executable.parent.mkdir(parents=True)
    executable.touch()
    older = tmp_path / "PostgreSQL" / "9" / "bin" / "pg_dump.exe"
    older.parent.mkdir(parents=True)
    older.touch()

    monkeypatch.delenv("PG_DUMP_PATH", raising=False)
    monkeypatch.setenv("ProgramFiles", str(tmp_path))
    monkeypatch.setattr(backup_database.shutil, "which", lambda command: None)

    assert backup_database._find_pg_dump() == str(executable)
