"""Read-only public-mode startup preflight; does not send email or open a port."""
import os

from fastapi.testclient import TestClient

os.environ.update({
    "CAPABILITY_DEPLOYMENT_MODE": "public",
    "CAPABILITY_REQUIRE_AUTH": "1",
    "CAPABILITY_PUBLIC_BASE_URL": "https://surfacedmp.com",
    "CAPABILITY_AUTH_DATABASE_URL": "postgresql:///advisor?host=/var/run/postgresql",
    "CAPABILITY_SMTP_HOST": "smtp.exmail.qq.com",
    "CAPABILITY_SMTP_FROM": "ls@yiheit.net",
    "CAPABILITY_SMTP_USERNAME": "ls@yiheit.net",
    "CAPABILITY_SMTP_PASSWORD": "preflight-only-never-used",
    "CAPABILITY_MFA_MASTER_KEY": "preflight-only-key-32-bytes-minimum-0001",
})
os.environ.pop("CAPABILITY_DEV_EXPOSE_TOKENS", None)

from app.main import app  # noqa: E402


def main() -> None:
    with TestClient(app, base_url="https://surfacedmp.com") as client:
        health = client.get("/health")
        assert health.status_code == 200, health.text
        assert health.json()["local"] is False
        assert client.get("/api/catalog/skus").status_code == 401
        assert client.get("/api/catalog/skus", headers={"Host": "untrusted.example"}).status_code == 400
    print("Public-mode local preflight passed: both stores and host/auth boundaries are ready.")


if __name__ == "__main__":
    main()
