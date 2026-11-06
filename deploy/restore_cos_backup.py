"""Drill an encrypted COS backup in an isolated, short-lived PostgreSQL database.

Run as root on the server. The live advisor database is never used as a target.
Plaintext files stay in a private temporary directory and are removed on exit.
"""

import argparse
from contextlib import closing
import io
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import tarfile
import tempfile

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from cos_offsite_backup import MAGIC, NAMES, COMMERCIAL_NAMES, cos_client, encryption_key
from verify_backup import safe_child_env, verify_backup


MAX_CIPHERTEXT = 256 * 1024 * 1024
OBJECT_KEY = re.compile(r"capability-advisor/[0-9]{8}T[0-9]{6}Z\.tar\.gcm\Z")
TABLES = ("organizations", "users", "licenses", "admin_mfa")


def decrypt_snapshot(encrypted: Path, destination: Path, key: bytes) -> None:
    if len(key) != 32 or encrypted.is_symlink() or not encrypted.is_file():
        raise ValueError("Invalid encrypted snapshot or backup key")
    if encrypted.stat().st_size > MAX_CIPHERTEXT:
        raise ValueError("Snapshot exceeds the 256 MiB drill limit")
    raw = encrypted.read_bytes()
    if not raw.startswith(MAGIC) or len(raw) < len(MAGIC) + 12 + 16:
        raise ValueError("Unknown encrypted backup format")
    offset = len(MAGIC)
    decryptor = Cipher(algorithms.AES(key), modes.GCM(raw[offset:offset + 12], raw[-16:])).decryptor()
    plaintext = decryptor.update(raw[offset + 12:-16]) + decryptor.finalize()
    with tarfile.open(fileobj=io.BytesIO(plaintext), mode="r:") as archive:
        members = archive.getmembers()
        if tuple(member.name for member in members) not in (NAMES,COMMERCIAL_NAMES):
            raise ValueError("Unexpected backup members")
        if any(not member.isfile() or member.size == 0 for member in members):
            raise ValueError("Unsafe backup member")
        destination.mkdir(mode=0o700)
        for member in members:
            source = archive.extractfile(member)
            if source is None:
                raise ValueError("Missing backup member")
            descriptor = os.open(destination / member.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "wb") as output:
                output.write(source.read())


def postgres_counts(database: str) -> dict[str, int]:
    counts = {}
    for table in TABLES:
        result = subprocess.run(
            ["runuser", "-u", "postgres", "--", "psql", "--dbname", database,
             "--tuples-only", "--no-align", "--command", f"SELECT count(*) FROM {table}"],
            check=True, capture_output=True, text=True, env=safe_child_env(),
        )
        counts[table] = int(result.stdout.strip())
    return counts


def drill(client, bucket: str, object_key: str, key: bytes) -> tuple[dict[str, int], int]:
    if os.geteuid() != 0:
        raise ValueError("The isolated restore drill must run as root")
    if not OBJECT_KEY.fullmatch(object_key):
        raise ValueError("Expected a timestamped Capability Advisor backup object")
    if not bucket or "/" in bucket:
        raise ValueError("Expected a COS bucket name")
    database = f"advisor_cos_restore_{os.urandom(6).hex()}"
    with tempfile.TemporaryDirectory(prefix="capability-cos-restore-") as temporary:
        root = Path(temporary)
        encrypted = root / "downloaded.tar.gcm"
        client.download_file(Bucket=bucket, Key=object_key, DestFilePath=str(encrypted))
        snapshot = root / "snapshot"
        decrypt_snapshot(encrypted, snapshot, key)
        verify_backup(snapshot)
        with closing(sqlite3.connect((snapshot / "capability.sqlite3").as_uri() + "?mode=ro", uri=True)) as catalog:
            sku_count = catalog.execute("SELECT count(*) FROM imported_skus").fetchone()[0]
        subprocess.run(
            ["runuser", "-u", "postgres", "--", "createdb", "--template=template0", database],
            check=True, capture_output=True, env=safe_child_env(),
        )
        try:
            with (snapshot / "accounts.dump").open("rb") as dump:
                subprocess.run(
                    ["runuser", "-u", "postgres", "--", "pg_restore", "--exit-on-error",
                     "--no-owner", "--no-acl", "--dbname", database],
                    stdin=dump, check=True, capture_output=True, env=safe_child_env(),
                )
            counts = postgres_counts(database)
        finally:
            subprocess.run(
                ["runuser", "-u", "postgres", "--", "dropdb", "--if-exists", database],
                check=True, capture_output=True, env=safe_child_env(),
            )
    return counts, sku_count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("object_key")
    args = parser.parse_args()
    rows, skus = drill(cos_client(), os.environ["CAPABILITY_COS_BUCKET"], args.object_key, encryption_key())
    print(f"Isolated COS restore passed; PostgreSQL row counts: {rows}; imported SKUs: {skus}")
