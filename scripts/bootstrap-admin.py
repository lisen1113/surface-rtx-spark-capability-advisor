"""Interactively create the first admin without exposing a password in argv or env."""
from getpass import getpass
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.auth import bootstrap_admin  # noqa: E402

def main() -> None:
    if not os.environ.get("CAPABILITY_AUTH_DATABASE_URL"):
        raise SystemExit("Set CAPABILITY_AUTH_DATABASE_URL to the intended private account database")
    if os.environ.get("CAPABILITY_ADMIN_PASSWORD"):
        raise SystemExit("Remove CAPABILITY_ADMIN_PASSWORD; enter the password interactively")
    if not sys.stdin.isatty():
        raise SystemExit("An interactive terminal is required")
    email = input("First administrator email: ").strip()
    password = getpass("New administrator password (hidden): ")
    confirmation = getpass("Repeat password (hidden): ")
    if password != confirmation:
        raise SystemExit("Passwords differ; no account was created")
    try:
        admin_id = bootstrap_admin(email, password)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    print(f"Administrator created with id {admin_id}. Enroll TOTP MFA at first sign-in.")


if __name__ == "__main__":
    main()
