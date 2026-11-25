"""Usage: backend/.venv/Scripts/python.exe scripts/import-v3-workbook.py <authorized.xlsx>"""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.xlsx_import import import_workbook  # noqa: E402


if len(sys.argv) != 2:
    raise SystemExit("Provide exactly one authorized .xlsx path")
print(json.dumps(import_workbook(sys.argv[1]), ensure_ascii=False, indent=2))
