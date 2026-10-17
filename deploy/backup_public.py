"""Create a private, point-in-time database and catalog backup on the server.

Run as the dedicated advisor account. Off-server encrypted copies and restore
drills are separate release requirements; this script does not claim them.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


CATALOG = Path("/opt/capability-advisor/data/capability.sqlite3")
BACKUP_ROOT = Path("/opt/capability-advisor/backups")


def safe_child_env() -> dict[str, str]:
    """Keep COS keys out of the pg_dump child process."""
    secrets = {"COS_SECRET_ID", "COS_SECRET_KEY", "COS_SESSION_TOKEN", "CAPABILITY_BACKUP_KEY_B64"}
    return {name: value for name, value in os.environ.items() if name not in secrets}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def create_backup(root: Path = BACKUP_ROOT, catalog: Path = CATALOG) -> Path:
    if not catalog.is_file() or catalog.is_symlink():
        raise ValueError("Expected a regular, local product catalog")
    if root.is_symlink():
        raise ValueError("Backup root cannot be a symlink")
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    if root.stat().st_mode & 0o077:
        raise ValueError("Backup root must not be accessible by other users")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = root / stamp
    destination.mkdir(mode=0o700)
    dump = destination / "accounts.dump"
    catalog_copy = destination / "capability.sqlite3"
    old_umask = os.umask(0o077)
    try:
        with dump.open("xb") as stream:
            subprocess.run(["pg_dump", "--format=custom", "--dbname=advisor"],
                           check=True, stdout=stream, stderr=subprocess.PIPE, env=safe_child_env())
        shutil.copyfile(catalog, catalog_copy)
        manifest = {
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "accounts_dump_sha256": sha256(dump),
            "catalog_sha256": sha256(catalog_copy),
        }
        (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    except BaseException:
        print("Backup incomplete; inspect the private destination before retrying", file=sys.stderr)
        raise
    finally:
        os.umask(old_umask)
    return destination


if __name__ == "__main__":
    print(f"Private backup created: {create_backup()}")
