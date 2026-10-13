"""Create the first admin from environment variables; no defaults are provided."""
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.auth import bootstrap_admin  # noqa: E402

email = os.environ.get("CAPABILITY_ADMIN_EMAIL")
password = os.environ.get("CAPABILITY_ADMIN_PASSWORD")
if not email or not password:
    raise SystemExit("Set CAPABILITY_ADMIN_EMAIL and CAPABILITY_ADMIN_PASSWORD before running this command")
admin_id = bootstrap_admin(email, password)
print(f"Admin created with id {admin_id}. Remove CAPABILITY_ADMIN_PASSWORD from the environment now.")
