import base64
import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[2] / "deploy" / "init_cos_env.py"
spec = importlib.util.spec_from_file_location("init_cos_env", SCRIPT)
initialization = importlib.util.module_from_spec(spec)
spec.loader.exec_module(initialization)


def test_renders_private_cos_configuration_without_application_secrets():
    backup_key = base64.b64encode(bytes(range(32))).decode()
    rendered = initialization.render_env(
        "advisorbucket-1350784604", "ap-shanghai", "id-value", "secret-value", backup_key
    )
    assert "CAPABILITY_COS_BUCKET=advisorbucket-1350784604" in rendered
    assert "CAPABILITY_COS_REGION=ap-shanghai" in rendered
    assert "CAPABILITY_BACKUP_KEY_B64=" in rendered
    assert "CAPABILITY_SMTP_PASSWORD" not in rendered


@pytest.mark.parametrize("bucket,region", [("bucket", "ap-shanghai"), ("bucket-123456", "Shanghai"),
                                           ("https://bucket-123456", "ap-shanghai")])
def test_rejects_invalid_bucket_or_region(bucket, region):
    key = base64.b64encode(bytes(range(32))).decode()
    with pytest.raises(ValueError):
        initialization.render_env(bucket, region, "id", "secret", key)


def test_rejects_short_backup_key():
    with pytest.raises(ValueError, match="32 bytes"):
        initialization.render_env("bucket-123456", "ap-shanghai", "id", "secret", "c2hvcnQ=")
