import runpy
import sqlite3
from pathlib import Path
from zipfile import ZipFile


def test_public_package_scrubs_accounts_and_contains_production_dependencies(tmp_path):
    script = Path(__file__).resolve().parents[2] / "scripts" / "build_public_package.py"
    builder = runpy.run_path(str(script))["build_package"]
    source = tmp_path / "source.sqlite3"
    with sqlite3.connect(source) as db:
        db.execute("CREATE TABLE imported_skus (part_number TEXT PRIMARY KEY)")
        db.execute("INSERT INTO imported_skus VALUES ('EP2-56792')")
        db.execute("CREATE TABLE source_records (record_json TEXT)")
        db.execute("CREATE TABLE users (email TEXT)")
        db.execute("INSERT INTO users VALUES ('private@example.invalid')")
    output = tmp_path / "public.zip"
    builder(source, output)
    with ZipFile(output) as archive:
        names = archive.namelist()
        assert "backend/app/auth_store.py" in names
        assert "backend/requirements-production.txt" in names
        assert "backend/sql/auth_postgres_v1.sql" in names
        assert all(not name.endswith((".xlsx", ".pem", ".env")) for name in names)
        content = archive.read("data/capability.sqlite3")
    assert b"private@example.invalid" not in content
