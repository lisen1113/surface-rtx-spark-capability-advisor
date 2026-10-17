"""Create a fresh private backup, then upload and read-verify its encrypted COS copy."""

from backup_public import create_backup
from cos_offsite_backup import cos_client, encryption_key, upload_verified
import os


def main() -> None:
    # Validate remote configuration before creating a new local backup.
    bucket = os.environ["CAPABILITY_COS_BUCKET"]
    key = encryption_key()
    client = cos_client()
    directory = create_backup()
    object_key = upload_verified(directory, client, bucket, key)
    print(f"Verified encrypted COS copy of {directory.name}: {object_key}")


if __name__ == "__main__":
    main()
