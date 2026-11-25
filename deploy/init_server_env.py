"""Run interactively with sudo on the dedicated server; never paste secrets into chat."""
from getpass import getpass
import os
from pathlib import Path
import secrets
import shlex


TARGET = Path("/etc/capability-advisor.env")


def render_env(smtp_password: str) -> str:
    if not smtp_password or any(ch in smtp_password for ch in "\r\n\x00"):
        raise ValueError("SMTP authorization code must be nonempty and single-line")
    values = {
        "CAPABILITY_DEPLOYMENT_MODE": "public",
        "CAPABILITY_REQUIRE_AUTH": "1",
        "CAPABILITY_PUBLIC_BASE_URL": "https://surfacedmp.com",
        "CAPABILITY_AUTH_DATABASE_URL": "postgresql:///advisor?host=/var/run/postgresql",
        "CAPABILITY_SMTP_HOST": "smtp.exmail.qq.com",
        "CAPABILITY_SMTP_PORT": "465",
        "CAPABILITY_SMTP_TLS_MODE": "ssl",
        "CAPABILITY_SMTP_FROM": "ls@yiheit.net",
        "CAPABILITY_SMTP_USERNAME": "ls@yiheit.net",
        "CAPABILITY_SMTP_PASSWORD": smtp_password,
        "CAPABILITY_MFA_MASTER_KEY": secrets.token_hex(32),
    }
    return "".join(f"{key}={shlex.quote(value)}\n" for key, value in values.items())


def main() -> None:
    if os.geteuid() != 0:
        raise SystemExit("Run with sudo on the dedicated server")
    if TARGET.exists():
        raise SystemExit("Configuration already exists; refusing to overwrite it")
    password = getpass("Paste the SMTP client authorization code (input hidden): ")
    confirm = getpass("Paste it again (input hidden): ")
    if password != confirm:
        raise SystemExit("Codes did not match; nothing was written")
    try:
        content = render_env(password)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    # Exclusive creation and restrictive mode avoid accidental replacement or
    # exposure to other local accounts. Never print the content.
    fd = os.open(TARGET, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(content)
    except BaseException:
        TARGET.unlink(missing_ok=True)
        raise
    print("Private environment file created; no secret was displayed.")


if __name__ == "__main__":
    main()
