"""Reject unsafe settings in shared and public deployments.

This is a configuration gate, not a security audit or deployment certificate.
"""

import os
from urllib.parse import urlsplit


def deployment_configuration_errors() -> list[str]:
    mode = os.getenv("CAPABILITY_DEPLOYMENT_MODE", "local")
    if mode == "local":
        return []
    if mode not in ("shared", "public"):
        return ["CAPABILITY_DEPLOYMENT_MODE must be local, shared, or public"]

    errors = []
    if mode == "public":
        if not os.getenv("CAPABILITY_AUTH_DATABASE_URL", "").startswith(("postgresql://", "postgres://")):
            errors.append("CAPABILITY_AUTH_DATABASE_URL must point to PostgreSQL")
    if os.getenv("CAPABILITY_REQUIRE_AUTH") != "1":
        errors.append("CAPABILITY_REQUIRE_AUTH must be 1")
    if os.getenv("CAPABILITY_DEV_EXPOSE_TOKENS") == "1":
        errors.append("CAPABILITY_DEV_EXPOSE_TOKENS must be disabled")
    if not os.getenv("CAPABILITY_SMTP_HOST") or not os.getenv("CAPABILITY_SMTP_FROM"):
        errors.append("SMTP host and sender must be configured")
    if mode == "public" and (not os.getenv("CAPABILITY_SMTP_USERNAME") or not os.getenv("CAPABILITY_SMTP_PASSWORD")):
        errors.append("SMTP username and credential must be configured")
    if os.getenv("CAPABILITY_SMTP_TLS_MODE", "starttls") not in ("starttls", "ssl"):
        errors.append("SMTP TLS mode must be starttls or ssl")
    if len(os.getenv("CAPABILITY_MFA_MASTER_KEY", "").encode("utf-8")) < 32:
        errors.append("CAPABILITY_MFA_MASTER_KEY must contain at least 32 bytes")

    public_url = os.getenv("CAPABILITY_PUBLIC_BASE_URL", "")
    try:
        parsed = urlsplit(public_url)
        valid_origin = (parsed.scheme == "https" and bool(parsed.hostname)
                        and not parsed.username and not parsed.password
                        and parsed.path in ("", "/") and not parsed.query and not parsed.fragment)
    except ValueError:
        valid_origin = False
    if not valid_origin:
        errors.append("CAPABILITY_PUBLIC_BASE_URL must be an HTTPS origin")
    return errors


def assert_deployment_configuration() -> None:
    errors = deployment_configuration_errors()
    if errors:
        raise RuntimeError("Deployment configuration incomplete: " + "; ".join(errors))
