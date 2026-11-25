import runpy
import sqlite3
from pathlib import Path
from zipfile import ZipFile


def test_staging_package_copies_catalog_without_accounts(tmp_path):
    script = Path(__file__).resolve().parents[2] / "scripts" / "build_staging_package.py"
    builder = runpy.run_path(str(script))["build_package"]
    source = tmp_path / "source.sqlite3"
    db = sqlite3.connect(source)
    try:
        db.execute("CREATE TABLE imported_skus (part_number TEXT PRIMARY KEY)")
        db.execute("INSERT INTO imported_skus VALUES ('EP2-56792')")
        db.execute("CREATE TABLE source_records (record_json TEXT)")
        db.execute("INSERT INTO source_records VALUES ('approved catalog record')")
        db.execute("CREATE TABLE users (email TEXT)")
        db.execute("INSERT INTO users VALUES ('secret@example.invalid')")
        db.execute("CREATE TABLE sessions (token_hash TEXT)")
        db.execute("INSERT INTO sessions VALUES ('secret-token')")
        db.commit()
    finally:
        db.close()
    output = tmp_path / "preview.zip"
    builder(source, output)
    with ZipFile(output) as archive:
        names = archive.namelist()
        assert "backend/app/main.py" in names
        assert "start-staging.sh" in names
        assert all(not name.endswith(".xlsx") for name in names)
        database = tmp_path / "scrubbed.sqlite3"
        database.write_bytes(archive.read("data/capability.sqlite3"))
    db = sqlite3.connect(database)
    try:
        assert db.execute("SELECT part_number FROM imported_skus").fetchone()[0] == "EP2-56792"
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert "users" not in tables
        assert "sessions" not in tables
    finally:
        db.close()
    assert b"secret@example.invalid" not in database.read_bytes()
    assert b"secret-token" not in database.read_bytes()
