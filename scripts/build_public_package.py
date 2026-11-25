"""Build a private public-server artifact without accounts, secrets or workbooks."""
from __future__ import annotations

import argparse
import runpy
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

_staging = runpy.run_path(str(Path(__file__).with_name("build_staging_package.py")))
ROOT = _staging["ROOT"]
copy_catalog = _staging["copy_catalog"]


def build_package(source_db: Path, output: Path) -> None:
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="advisor-public-", dir=output.parent) as temp:
        catalog = Path(temp) / "capability.sqlite3"
        copy_catalog(source_db.resolve(), catalog)
        with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
            for path in sorted((ROOT / "backend" / "app").rglob("*")):
                if path.is_file() and (path.suffix == ".py" or "assets" in path.parts):
                    archive.write(path, path.relative_to(ROOT))
            for name in ("requirements.txt", "requirements-production.txt"):
                archive.write(ROOT / "backend" / name, "backend/" + name)
            archive.write(ROOT / "backend" / "sql" / "auth_postgres_v1.sql", "backend/sql/auth_postgres_v1.sql")
            archive.write(catalog, "data/capability.sqlite3")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-db", type=Path, default=ROOT / "data" / "capability.sqlite3")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build_package(args.source_db, args.output)
    print(f"Private public-server package created: {args.output.resolve()}")
