import importlib.util
import json
from pathlib import Path
import sqlite3

import pytest


SCRIPT = Path(__file__).resolve().parents[2] / "deploy" / "verify_backup.py"
spec = importlib.util.spec_from_file_location("verify_backup", SCRIPT)
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


def backup_fixture(tmp_path):
    directory = tmp_path / "private"
    directory.mkdir(mode=0o700)
    dump = directory / "accounts.dump"
    dump.write_bytes(b"test archive")
    catalog = directory / "capability.sqlite3"
    with sqlite3.connect(catalog) as db:
        db.execute("CREATE TABLE imported_skus (part_number TEXT)")
        db.execute("INSERT INTO imported_skus VALUES ('TEST-SKU')")
    manifest = {"accounts_dump_sha256": verifier.sha256(dump),
                "catalog_sha256": verifier.sha256(catalog)}
    (directory / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return directory


def test_validates_manifest_catalog_and_dump(tmp_path, monkeypatch):
    directory = backup_fixture(tmp_path)
    calls = []
    monkeypatch.setattr(verifier.subprocess, "run", lambda args, **kwargs: calls.append(args))
    verifier.verify_backup(directory)
    assert calls == [["pg_restore", "--list", str(directory / "accounts.dump")]]


def test_rejects_tampered_dump_before_restore_listing(tmp_path, monkeypatch):
    directory = backup_fixture(tmp_path)
    (directory / "accounts.dump").write_bytes(b"tampered")
    monkeypatch.setattr(verifier.subprocess, "run", lambda *args, **kwargs: pytest.fail("unexpected pg_restore"))
    with pytest.raises(ValueError, match="dump checksum mismatch"):
        verifier.verify_backup(directory)


def test_rejects_tampered_catalog(tmp_path, monkeypatch):
    directory = backup_fixture(tmp_path)
    (directory / "capability.sqlite3").write_bytes(b"tampered")
    monkeypatch.setattr(verifier.subprocess, "run", lambda *args, **kwargs: pytest.fail("unexpected pg_restore"))
    with pytest.raises(ValueError, match="Catalog checksum mismatch"):
        verifier.verify_backup(directory)
