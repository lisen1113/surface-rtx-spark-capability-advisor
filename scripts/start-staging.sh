#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
if [ "$(id -u)" -eq 0 ]; then
  echo "Run as the unprivileged ubuntu user, not root." >&2
  exit 1
fi
if [ ! -f data/capability.sqlite3 ]; then
  echo "Catalog database missing; preview package is incomplete." >&2
  exit 1
fi

python3 -m venv .venv
.venv/bin/python -m pip install --disable-pip-version-check -r backend/requirements.txt
export CAPABILITY_DEPLOYMENT_MODE=local
export CAPABILITY_REQUIRE_AUTH=0
exec .venv/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8011
