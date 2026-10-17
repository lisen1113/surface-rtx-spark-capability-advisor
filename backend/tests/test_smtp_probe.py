import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[2] / "deploy" / "smtp_probe.py"
spec = importlib.util.spec_from_file_location("smtp_probe", SCRIPT)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def test_probe_rejects_unexpected_destination_before_network(monkeypatch):
    monkeypatch.setenv("CAPABILITY_SMTP_FROM", "other@example.com")
    monkeypatch.setenv("CAPABILITY_SMTP_USERNAME", "other@example.com")
    monkeypatch.setattr(probe.smtplib, "SMTP_SSL", lambda *_args, **_kwargs: pytest.fail("network attempted"))
    with pytest.raises(SystemExit, match="limited to the configured sender"):
        probe.main()


def test_probe_sends_only_to_self(monkeypatch):
    monkeypatch.setenv("CAPABILITY_SMTP_FROM", "ls@yiheit.net")
    monkeypatch.setenv("CAPABILITY_SMTP_USERNAME", "ls@yiheit.net")
    monkeypatch.setenv("CAPABILITY_SMTP_PASSWORD", "private-test-value")
    monkeypatch.setenv("CAPABILITY_SMTP_TLS_MODE", "ssl")
    monkeypatch.setenv("CAPABILITY_SMTP_HOST", "smtp.exmail.qq.com")
    sent = []

    class FakeSMTP:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            pass

        def login(self, username, password):
            assert username == "ls@yiheit.net"
            assert password == "private-test-value"

        def send_message(self, message):
            sent.append(message)

    monkeypatch.setattr(probe.smtplib, "SMTP_SSL", lambda *_args, **_kwargs: FakeSMTP())
    probe.main()
    assert len(sent) == 1
    assert sent[0]["To"] == sent[0]["From"] == "ls@yiheit.net"
    assert "private-test-value" not in sent[0].as_string()
