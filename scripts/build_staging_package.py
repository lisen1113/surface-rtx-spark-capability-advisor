"""Build a loopback-only preview package without accounts or source workbooks.

The output is a private deployment artifact, not a file to commit or publish.
"""

from __future__ import annotations

import argparse
import sqlite3
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
CATALOG_TABLES = (
    "skus", "models", "evidence", "source_imports", "source_records",
    "imported_skus", "imported_evidence", "sku_lookup",
)
REQUIRED_TABLES = {"source_records", "imported_skus"}


def copy_catalog(source_db: Path, target_db: Path) -> None:
    if not source_db.is_file():
        raise FileNotFoundError(f"Catalog database not found: {source_db}")
    source = sqlite3.connect(source_db.as_uri() + "?mode=ro", uri=True)
    destination = sqlite3.connect(target_db)
    try:
        present = {
            row[0]: row[1]
            for row in source.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
            if row[1]
        }
        missing = REQUIRED_TABLES - present.keys()
        if missing:
            raise ValueError(f"Catalog tables missing: {', '.join(sorted(missing))}")
        for table in CATALOG_TABLES:
            if table not in present:
                continue
            destination.execute(present[table])
            rows = source.execute(f'SELECT * FROM "{table}"').fetchall()
            if rows:
                marks = ",".join("?" for _ in rows[0])
                destination.executemany(f'INSERT INTO "{table}" VALUES ({marks})', rows)
        destination.commit()
        if destination.execute("SELECT COUNT(*) FROM imported_skus").fetchone()[0] == 0:
            raise ValueError("No imported SKUs; refusing to build an empty preview")
        destination.execute("VACUUM")
    finally:
        destination.close()
        source.close()


def build_package(source_db: Path, output: Path) -> None:
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="advisor-staging-", dir=output.parent) as temp:
        scrubbed_db = Path(temp) / "capability.sqlite3"
        copy_catalog(source_db.resolve(), scrubbed_db)
        with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
            for path in sorted((ROOT / "backend" / "app").rglob("*")):
                if path.is_file() and (path.suffix == ".py" or "assets" in path.parts):
                    archive.write(path, path.relative_to(ROOT))
            archive.write(ROOT / "backend" / "requirements.txt", "backend/requirements.txt")
            archive.write(ROOT / "scripts" / "start-staging.sh", "start-staging.sh")
            archive.write(scrubbed_db, "data/capability.sqlite3")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-db", type=Path, default=ROOT / "data" / "capability.sqlite3")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build_package(args.source_db, args.output)
    print(f"Private loopback preview package created: {args.output.resolve()}")
