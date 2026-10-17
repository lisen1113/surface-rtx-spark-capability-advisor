"""Read-only checks for a private backup; not a substitute for a restore drill."""

import argparse
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_backup(directory: Path) -> None:
    if directory.is_symlink():
        raise ValueError("Backup directory cannot be a symlink")
    directory = directory.resolve(strict=True)
    if not directory.is_dir() or (os.name != "nt" and directory.stat().st_mode & 0o077):
        raise ValueError("Backup directory must be private")
    manifest_path = directory / "manifest.json"
    dump = directory / "accounts.dump"
    catalog = directory / "capability.sqlite3"
    for path in (manifest_path, dump, catalog):
        if path.is_symlink() or not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f"Missing or unsafe backup file: {path.name}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if sha256(dump) != manifest["accounts_dump_sha256"]:
        raise ValueError("PostgreSQL dump checksum mismatch")
    if sha256(catalog) != manifest["catalog_sha256"]:
        raise ValueError("Catalog checksum mismatch")
    subprocess.run(["pg_restore", "--list", str(dump)], check=True, capture_output=True)
    with closing(sqlite3.connect(catalog.as_uri() + "?mode=ro", uri=True)) as db:
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("Catalog integrity check failed")
        db.execute("SELECT 1 FROM imported_skus LIMIT 1")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="Private backup directory to inspect")
    args = parser.parse_args()
    verify_backup(args.directory)
    print("Backup checksum and structure verified; a separate restore drill is still required.")
