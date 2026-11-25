"""Build an isolated local catalog/identity workspace; never touches source DBs."""
import argparse
from datetime import timedelta
import importlib.util
import json
import os
from pathlib import Path
import secrets
import sys

ROOT = Path(__file__).resolve().parents[1]


def prepare(source, target):
    source, target = source.resolve(), target.resolve()
    target.mkdir(parents=True, exist_ok=True)
    catalog_target = target / "catalog.sqlite3"
    if source == catalog_target:
        raise ValueError("Source catalog must not be the development destination")
    if not catalog_target.exists():
        spec = importlib.util.spec_from_file_location("staging_copy", ROOT / "scripts" / "build_staging_package.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.copy_catalog(source, catalog_target)
    os.environ["CAPABILITY_DEPLOYMENT_MODE"] = "local"
    os.environ["CAPABILITY_CATALOG_PATH"] = str(catalog_target)
    os.environ.pop("CAPABILITY_AUTH_DATABASE_URL", None)
    sys.path.insert(0, str(ROOT / "backend"))
    from app.auth import hasher, iso, now
    from app.catalog import connection
    credentials_path = target / "credentials.json"
    if not credentials_path.exists():
        credentials = {}
        with connection() as conn:
            for role, email in (("owner", "preview-customer@local.example"), ("admin", "preview-admin@local.example")):
                password = secrets.token_urlsafe(24)
                created = iso(now())
                org = conn.execute("INSERT INTO organizations(name,status,created_at) VALUES(?,'approved',?)", ("本地演示组织 " + role, created)).lastrowid
                conn.execute("INSERT INTO users(organization_id,email,password_hash,role,status,email_verified,created_at,approved_at) VALUES(?,?,?,?,'approved',1,?,?)", (org, email, hasher.hash(password), role, created, created))
                conn.execute("INSERT INTO licenses VALUES(?,?,?,'active',?)", (org, 10, iso(now() + timedelta(days=365)), created))
                credentials[role] = {"email": email, "password": password, "organization_id": org}
            conn.commit()
        credentials_path.write_text(json.dumps(credentials, ensure_ascii=False, indent=2), encoding="utf-8")
        credentials_path.chmod(0o600)
    with connection() as conn:
        lookup_count = conn.execute("SELECT COUNT(*) FROM sku_lookup").fetchone()[0]
        spark_count = conn.execute("SELECT COUNT(*) FROM imported_skus").fetchone()[0]
    print(json.dumps({"workspace": str(target), "lookup_count": lookup_count, "existing_capability_count": spark_count,
                      "credentials_file": str(credentials_path), "note": "Random local credentials only; source accounts were not copied"}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "data" / "sku-preview.sqlite3")
    parser.add_argument("--directory", type=Path, default=ROOT / ".commercial-local")
    args = parser.parse_args()
    prepare(args.source, args.directory)
