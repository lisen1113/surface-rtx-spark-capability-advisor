"""Isolated COS restore drill must authenticate data and never target production."""

import importlib.util
import os
from pathlib import Path
import sys

import pytest
from cryptography.exceptions import InvalidTag

pytest.importorskip("cryptography")
DEPLOY = Path(__file__).resolve().parents[2] / "deploy"
sys.path.insert(0, str(DEPLOY))
spec = importlib.util.spec_from_file_location("restore_cos_backup", DEPLOY / "restore_cos_backup.py")
restore = importlib.util.module_from_spec(spec)
spec.loader.exec_module(restore)
from test_cos_offsite_backup import fixture


def encrypted_fixture(tmp_path, monkeypatch):
    source = fixture(tmp_path)
    monkeypatch.setattr(restore, "verify_backup", lambda path: None)
    monkeypatch.setattr(sys.modules["cos_offsite_backup"], "verify_backup", lambda path: None)
    encrypted = tmp_path / "backup.gcm"
    key = os.urandom(32)
    sys.modules["cos_offsite_backup"].encrypt_backup(source, encrypted, key)
    return encrypted, key


def test_decrypts_only_expected_files_in_private_directory(tmp_path, monkeypatch):
    encrypted, key = encrypted_fixture(tmp_path, monkeypatch)
    destination = tmp_path / "restored"
    restore.decrypt_snapshot(encrypted, destination, key)
    assert sorted(path.name for path in destination.iterdir()) == sorted(restore.NAMES)
    assert (destination / "accounts.dump").read_bytes() == b"database archive"
    if os.name != "nt":
        assert destination.stat().st_mode & 0o077 == 0
        assert all(path.stat().st_mode & 0o077 == 0 for path in destination.iterdir())


def test_rejects_tampered_ciphertext_before_writing_plaintext(tmp_path, monkeypatch):
    encrypted, key = encrypted_fixture(tmp_path, monkeypatch)
    raw = bytearray(encrypted.read_bytes())
    raw[-17] ^= 1
    encrypted.write_bytes(raw)
    with pytest.raises(InvalidTag):
        restore.decrypt_snapshot(encrypted, tmp_path / "restored", key)
    assert not (tmp_path / "restored").exists()


def test_rejects_unexpected_object_key_before_download(tmp_path, monkeypatch):
    monkeypatch.setattr(restore.os, "geteuid", lambda: 0, raising=False)

    class FakeCOS:
        def download_file(self, **kwargs):
            pytest.fail("unexpected COS download")

    with pytest.raises(ValueError, match="timestamped"):
        restore.drill(FakeCOS(), "bucket-1350784604", "../../bad.tar.gcm", os.urandom(32))


def test_drill_uses_disposable_database_and_cleans_up(tmp_path, monkeypatch):
    encrypted, key = encrypted_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(restore.os, "geteuid", lambda: 0, raising=False)
    monkeypatch.setattr(restore, "postgres_counts", lambda database: {"users": 2})
    commands = []

    def fake_run(command, **kwargs):
        commands.append(command)
        return None

    monkeypatch.setattr(restore.subprocess, "run", fake_run)

    class FakeCOS:
        def download_file(self, **kwargs):
            Path(kwargs["DestFilePath"]).write_bytes(encrypted.read_bytes())

    rows, skus = restore.drill(
        FakeCOS(), "bucket-1350784604", "capability-advisor/20261017T090059Z.tar.gcm", key
    )
    assert rows == {"users": 2}
    assert skus == 0
    assert commands[0][-1].startswith("advisor_cos_restore_")
    assert commands[1][-1] == commands[0][-1]
    assert commands[2][-1] == commands[0][-1]
    assert all("--dbname=advisor" not in part for command in commands for part in command)
