import runpy
from pathlib import Path

import pytest


def test_server_env_quotes_secret_without_printing_it():
    script = Path(__file__).resolve().parents[2] / "deploy" / "init_server_env.py"
    render = runpy.run_path(str(script))["render_env"]
    content = render("safe'code$123")
    assert "CAPABILITY_SMTP_FROM=ls@yiheit.net" in content
    assert "CAPABILITY_SMTP_PASSWORD='safe'\"'\"'code$123'" in content
    assert "CAPABILITY_MFA_MASTER_KEY=" in content
    with pytest.raises(ValueError):
        render("bad\ncode")
