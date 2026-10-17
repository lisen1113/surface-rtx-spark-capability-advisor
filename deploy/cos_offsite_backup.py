"""Encrypt a verified backup before COS upload and verify a downloaded copy.

This command never creates or deletes a COS bucket. Keep its 32-byte encryption
key outside the server backup directory and escrow it separately from COS access.
"""

import argparse
import base64
import hashlib
import io
import os
from pathlib import Path
import tarfile
import tempfile

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from verify_backup import verify_backup


MAGIC = b"CAD-COS-1\n"
NAMES = ("manifest.json", "accounts.dump", "capability.sqlite3")


def encryption_key() -> bytes:
    key = base64.b64decode(os.environ["CAPABILITY_BACKUP_KEY_B64"], validate=True)
    if len(key) != 32:
        raise ValueError("CAPABILITY_BACKUP_KEY_B64 must encode exactly 32 bytes")
    return key


class EncryptWriter:
    def __init__(self, stream, encryptor):
        self.stream, self.encryptor = stream, encryptor

    def write(self, data):
        self.stream.write(self.encryptor.update(data))
        return len(data)

    def flush(self):
        self.stream.flush()


def encrypt_backup(directory: Path, output: Path, key: bytes) -> str:
    if len(key) != 32:
        raise ValueError("Backup encryption requires a 32-byte key")
    verify_backup(directory)
    if output.exists() or output.is_symlink():
        raise ValueError("Encrypted output already exists")
    nonce = os.urandom(12)
    encryptor = Cipher(algorithms.AES(key), modes.GCM(nonce)).encryptor()
    old_umask = os.umask(0o077)
    try:
        with output.open("xb") as stream:
            stream.write(MAGIC + nonce)
            with tarfile.open(fileobj=EncryptWriter(stream, encryptor), mode="w|") as archive:
                for name in NAMES:
                    archive.add(directory / name, arcname=name, recursive=False)
            stream.write(encryptor.finalize() + encryptor.tag)
        digest = hashlib.sha256()
        with output.open("rb") as encrypted:
            for chunk in iter(lambda: encrypted.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    finally:
        os.umask(old_umask)


def verify_encrypted(path: Path, key: bytes, expected_sha256: str) -> None:
    if len(key) != 32:
        raise ValueError("Backup decryption requires a 32-byte key")
    if path.is_symlink() or not path.is_file():
        raise ValueError("Downloaded backup must be a regular file")
    if path.stat().st_size > 256 * 1024 * 1024:
        raise ValueError("Backup exceeds this verifier's 256 MiB memory safety limit")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("Downloaded ciphertext checksum mismatch")
    if not raw.startswith(MAGIC) or len(raw) < len(MAGIC) + 12 + 16:
        raise ValueError("Unknown encrypted backup format")
    start = len(MAGIC)
    decryptor = Cipher(algorithms.AES(key), modes.GCM(raw[start:start + 12], raw[-16:])).decryptor()
    plaintext = decryptor.update(raw[start + 12:-16]) + decryptor.finalize()
    with tarfile.open(fileobj=io.BytesIO(plaintext), mode="r:") as archive:
        if tuple(member.name for member in archive.getmembers()) != NAMES:
            raise ValueError("Unexpected backup members")
        for member in archive.getmembers():
            if not member.isfile() or member.size == 0:
                raise ValueError("Invalid backup member")


def cos_client():
    from qcloud_cos import CosConfig, CosS3Client

    config = CosConfig(
        Region=os.environ["CAPABILITY_COS_REGION"],
        SecretId=os.environ["COS_SECRET_ID"],
        SecretKey=os.environ["COS_SECRET_KEY"],
        Token=os.environ.get("COS_SESSION_TOKEN"),
        Scheme="https",
    )
    return CosS3Client(config)


def upload_verified(directory: Path, client, bucket: str, key: bytes) -> str:
    if not bucket or "/" in bucket:
        raise ValueError("Expected a COS bucket name, not a URL")
    if not directory.name.endswith("Z") or not directory.name[:-1].replace("T", "").isdigit():
        raise ValueError("Backup directory must have a UTC timestamp name")
    object_key = f"capability-advisor/{directory.name}.tar.gcm"
    with tempfile.TemporaryDirectory(prefix="capability-cos-") as temporary:
        encrypted = Path(temporary) / "backup.tar.gcm"
        digest = encrypt_backup(directory, encrypted, key)
        # The verifier is capped at 256 MiB, so a single PUT keeps CAM scope
        # limited to PutObject rather than multipart-upload permissions.
        with encrypted.open("rb") as stream:
            client.put_object(Bucket=bucket, Key=object_key, Body=stream)
        downloaded = Path(temporary) / "downloaded.tar.gcm"
        client.download_file(Bucket=bucket, Key=object_key, DestFilePath=str(downloaded))
        verify_encrypted(downloaded, key, digest)
    return object_key


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    remote_key = upload_verified(args.directory, cos_client(), os.environ["CAPABILITY_COS_BUCKET"], encryption_key())
    print(f"Encrypted COS backup uploaded and downloaded for verification: {remote_key}")
