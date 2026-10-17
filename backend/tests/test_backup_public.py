import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[2] / "deploy" / "backup_public.py"
spec = importlib.util.spec_from_file_location("backup_public", SCRIPT)
backup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backup)


def test_sha256_streams_file(tmp_path):
    source = tmp_path / "catalog"
    source.write_bytes(b"abc")
    assert backup.sha256(source) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_refuses_missing_catalog_before_creating_backup(tmp_path):
    root = tmp_path / "backup"
    with pytest.raises(ValueError, match="regular, local product catalog"):
        backup.create_backup(root, tmp_path / "missing")
    assert not root.exists()


def test_refuses_catalog_symlink(tmp_path):
    source = tmp_path / "actual"
    source.write_bytes(b"abc")
    link = tmp_path / "link"
    try:
        link.symlink_to(source)
    except OSError:
        pytest.skip("Symlinks unavailable on this host")
    with pytest.raises(ValueError, match="regular, local product catalog"):
        backup.create_backup(tmp_path / "backup", link)
