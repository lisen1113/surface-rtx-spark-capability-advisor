"""Create a root-only COS backup configuration from hidden terminal inputs."""

import argparse
import base64
import binascii
from getpass import getpass
import os
from pathlib import Path
import re
import shlex


TARGET = Path("/etc/capability-cos-backup.env")


def render_env(bucket: str, region: str, secret_id: str, secret_key: str, backup_key: str) -> str:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*-\d{5,}", bucket):
        raise ValueError("Expected a full COS BucketName-APPID")
    if not re.fullmatch(r"[a-z]{2}-[a-z0-9-]+", region):
        raise ValueError("Expected a COS region code")
    for name, value in (("SecretId", secret_id), ("SecretKey", secret_key), ("backup key", backup_key)):
        if not value or any(character in value for character in "\r\n\x00"):
            raise ValueError(f"{name} must be nonempty and single-line")
    try:
        if len(base64.b64decode(backup_key, validate=True)) != 32:
            raise ValueError("Backup key must encode exactly 32 bytes")
    except (ValueError, binascii.Error) as error:
        raise ValueError("Backup key must be Base64 of exactly 32 bytes") from error
    values = {
        "CAPABILITY_COS_BUCKET": bucket,
        "CAPABILITY_COS_REGION": region,
        "COS_SECRET_ID": secret_id,
        "COS_SECRET_KEY": secret_key,
        "CAPABILITY_BACKUP_KEY_B64": backup_key,
    }
    return "".join(f"{name}={shlex.quote(value)}\n" for name, value in values.items())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bucket")
    parser.add_argument("region")
    args = parser.parse_args()
    if os.geteuid() != 0:
        raise SystemExit("Run with sudo on the dedicated server")
    if TARGET.exists() or TARGET.is_symlink():
        raise SystemExit("COS backup configuration already exists; refusing to overwrite it")
    secret_id = getpass("COS limited-account SecretId (hidden): ")
    secret_key = getpass("COS limited-account SecretKey (hidden): ")
    backup_key = getpass("Escrowed 32-byte backup key in Base64 (hidden): ")
    confirmation = getpass("Repeat backup key (hidden): ")
    if backup_key != confirmation:
        raise SystemExit("Backup keys differ; nothing was written")
    try:
        content = render_env(args.bucket, args.region, secret_id, secret_key, backup_key)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    descriptor = os.open(TARGET, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(content)
    except BaseException:
        TARGET.unlink(missing_ok=True)
        raise
    print("Root-only COS backup configuration created; no credential was displayed.")


if __name__ == "__main__":
    main()
