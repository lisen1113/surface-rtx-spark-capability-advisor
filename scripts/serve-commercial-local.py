"""Serve the private commercial preview on loopback with isolated stores."""
import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=ROOT / ".commercial-local")
    parser.add_argument("--port", type=int, default=8020)
    args = parser.parse_args()
    directory = args.directory.resolve()
    if not (directory / "catalog.sqlite3").is_file():
        raise SystemExit("Run prepare-commercial-local.py first")
    os.environ["CAPABILITY_DEPLOYMENT_MODE"] = "local"
    # Keep the existing loopback evaluation behavior. Commercial endpoints always
    # require a real approved session and active organization license themselves.
    # This avoids changing the site's existing MFA setup just to run a local demo.
    os.environ["CAPABILITY_REQUIRE_AUTH"] = "0"
    os.environ["CAPABILITY_CATALOG_PATH"] = str(directory / "catalog.sqlite3")
    if not (directory / "identity.sqlite3").exists():
        raise SystemExit("Run prepare-commercial-public.py first")
    os.environ["CAPABILITY_AUTH_SQLITE_PATH"] = str(directory / "identity.sqlite3")
    os.environ["CAPABILITY_COMMERCIAL_PATH"] = str(directory / "commercial-public.sqlite3")
    os.environ.pop("CAPABILITY_AUTH_DATABASE_URL", None)
    os.environ.pop("CAPABILITY_DEV_EXPOSE_TOKENS", None)
    sys.path.insert(0, str(ROOT / "backend"))
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=args.port)
