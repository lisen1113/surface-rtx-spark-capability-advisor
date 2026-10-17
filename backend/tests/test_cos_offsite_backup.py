import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import sys

import pytest


pytest.importorskip("cryptography")
from cryptography.exceptions import InvalidTag
DEPLOY = Path(__file__).resolve().parents[2] / "deploy"
sys.path.insert(0, str(DEPLOY))
spec = importlib.util.spec_from_file_location("cos_offsite_backup", DEPLOY / "cos_offsite_backup.py")
backup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backup)


def fixture(tmp_path):
    directory = tmp_path / "20261017T090059Z"
    directory.mkdir(mode=0o700)
    (directory / "accounts.dump").write_bytes(b"database archive")
    with sqlite3.connect(directory / "capability.sqlite3") as db:
        db.execute("CREATE TABLE imported_skus (part_number TEXT)")
    manifest = {
        "accounts_dump_sha256": backup.hashlib.sha256((directory / "accounts.dump").read_bytes()).hexdigest(),
        "catalog_sha256": backup.hashlib.sha256((directory / "capability.sqlite3").read_bytes()).hexdigest(),
    }
    (directory / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return directory


def test_upload_download_authenticates_encrypted_snapshot(tmp_path, monkeypatch):
    directory = fixture(tmp_path)
    monkeypatch.setattr(backup, "verify_backup", lambda path: None)
    objects = {}

    class FakeCOS:
        def put_object(self, **kwargs):
            objects[kwargs["Key"]] = kwargs["Body"].read()

        def download_file(self, **kwargs):
            Path(kwargs["DestFilePath"]).write_bytes(objects[kwargs["Key"]])

    key = os.urandom(32)
    object_key = backup.upload_verified(directory, FakeCOS(), "private-1250000000", key)
    assert object_key == "capability-advisor/20261017T090059Z.tar.gcm"
    assert b"database archive" not in objects[object_key]


def test_rejects_ciphertext_tampering(tmp_path, monkeypatch):
    directory = fixture(tmp_path)
    monkeypatch.setattr(backup, "verify_backup", lambda path: None)
    encrypted = tmp_path / "copy.gcm"
    key = os.urandom(32)
    digest = backup.encrypt_backup(directory, encrypted, key)
    raw = bytearray(encrypted.read_bytes())
    raw[30] ^= 1
    encrypted.write_bytes(raw)
    with pytest.raises(ValueError, match="checksum mismatch"):
        backup.verify_encrypted(encrypted, key, digest)
    with pytest.raises(InvalidTag):
        backup.verify_encrypted(encrypted, key, backup.hashlib.sha256(raw).hexdigest())


def test_rejects_short_encryption_key(tmp_path):
    with pytest.raises(ValueError, match="32-byte key"):
        backup.encrypt_backup(tmp_path, tmp_path / "copy.gcm", b"short")


def test_rejects_invalid_bucket_before_upload(tmp_path):
    with pytest.raises(ValueError, match="bucket name"):
        backup.upload_verified(tmp_path, None, "https://cos.example", os.urandom(32))
