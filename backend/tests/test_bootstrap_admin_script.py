"""The production bootstrap must never accept credentials via shell history."""
import importlib.util
from pathlib import Path
import sys

import pytest


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "bootstrap-admin.py"
spec = importlib.util.spec_from_file_location("bootstrap_admin_script", SCRIPT)
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)


def test_requires_private_database_and_terminal(monkeypatch):
    monkeypatch.delenv("CAPABILITY_AUTH_DATABASE_URL", raising=False)
    with pytest.raises(SystemExit, match="CAPABILITY_AUTH_DATABASE_URL"):
        bootstrap.main()
    monkeypatch.setenv("CAPABILITY_AUTH_DATABASE_URL", "postgresql:///advisor")
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    with pytest.raises(SystemExit, match="interactive terminal"):
        bootstrap.main()


def test_refuses_password_environment_variable(monkeypatch):
    monkeypatch.setenv("CAPABILITY_AUTH_DATABASE_URL", "postgresql:///advisor")
    monkeypatch.setenv("CAPABILITY_ADMIN_PASSWORD", "should-never-be-accepted")
    with pytest.raises(SystemExit, match="Remove CAPABILITY_ADMIN_PASSWORD"):
        bootstrap.main()


def test_password_confirmation_precedes_database_write(monkeypatch):
    monkeypatch.setenv("CAPABILITY_AUTH_DATABASE_URL", "postgresql:///advisor")
    monkeypatch.delenv("CAPABILITY_ADMIN_PASSWORD", raising=False)
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda _prompt: "admin@example.com")
    passwords = iter(["long-password-first", "long-password-second"])
    monkeypatch.setattr(bootstrap, "getpass", lambda _prompt: next(passwords))
    monkeypatch.setattr(bootstrap, "bootstrap_admin", lambda *_args: pytest.fail("database write attempted"))
    with pytest.raises(SystemExit, match="Passwords differ"):
        bootstrap.main()
