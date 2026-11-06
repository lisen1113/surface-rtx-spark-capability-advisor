"""Apply the reviewed Surface lookup update while preserving the live catalog and auth."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import pwd
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from zipfile import ZipFile

ROOT = Path('/opt/capability-advisor')
FILES = ('backend/app/catalog.py', 'backend/app/ui.py', 'backend/app/surface_pdf.py',
         'backend/app/report.py', 'backend/app/auth_ui.py', 'backend/app/branding.py',
         'backend/app/guest_ui.py', 'backend/app/deployment.py',
         'backend/app/assets/theme.css', 'backend/app/assets/microsoft-surface.png')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main(archive_path, expected_sha):
    archive = Path(archive_path).resolve()
    assert digest(archive) == expected_sha.lower(), 'Upload checksum mismatch'
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup = ROOT / 'backups' / ('surface-release-' + stamp)
    backup.mkdir(mode=0o700)
    catalog = ROOT / 'data/capability.sqlite3'
    with sqlite3.connect(catalog) as source, sqlite3.connect(backup / 'capability.sqlite3') as target:
        source.backup(target)
        before_count = source.execute('SELECT COUNT(*) FROM imported_skus').fetchone()[0]
    original_files = {}
    for name in FILES:
        source = ROOT / name
        original_files[name] = source.exists()
        if source.exists():
            target = backup / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    account = pwd.getpwnam('advisor')
    installed = False
    try:
        with tempfile.TemporaryDirectory(prefix='surface-release-', dir=ROOT / 'data') as temporary:
            temporary = Path(temporary)
            with ZipFile(archive) as package:
                for name in FILES + ('data/capability.sqlite3',):
                    target = temporary / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(package.read(name))
                for name in FILES:
                    if name.endswith('.py'):
                        compile((temporary / name).read_text(encoding='utf-8'), name, 'exec')
            candidate = temporary / 'merged.sqlite3'
            with sqlite3.connect(catalog) as source, sqlite3.connect(candidate) as target:
                source.backup(target)
            with sqlite3.connect(temporary / 'data/capability.sqlite3') as incoming, sqlite3.connect(candidate) as target:
                table_schema = incoming.execute("SELECT sql FROM sqlite_master WHERE name='sku_lookup'").fetchone()[0]
                target.execute(table_schema.replace('CREATE TABLE', 'CREATE TABLE IF NOT EXISTS', 1))
                target.execute('DELETE FROM sku_lookup')
                records = incoming.execute('SELECT * FROM sku_lookup').fetchall()
                target.executemany('INSERT INTO sku_lookup VALUES (' + ','.join('?' for _ in records[0]) + ')', records)
                hashes = {row[0] for row in incoming.execute('SELECT DISTINCT source_sha256 FROM sku_lookup')}
                for source_hash in hashes:
                    target.execute('DELETE FROM source_records WHERE source_sha256=?', (source_hash,))
                    target.executemany('INSERT INTO source_records VALUES (?,?,?,?)', incoming.execute('SELECT * FROM source_records WHERE source_sha256=?', (source_hash,)).fetchall())
                    target.execute('DELETE FROM source_imports WHERE source_sha256=?', (source_hash,))
                    target.executemany('INSERT INTO source_imports VALUES (?,?,?,?,?,?)', incoming.execute('SELECT * FROM source_imports WHERE source_sha256=?', (source_hash,)).fetchall())
                target.commit()
                assert target.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
                assert target.execute('SELECT COUNT(*) FROM sku_lookup').fetchone()[0] == 237
                assert target.execute('SELECT COUNT(*) FROM imported_skus').fetchone()[0] == before_count
            subprocess.run(['systemctl', 'stop', 'capability-advisor'], check=True)
            installed = True
            for name in FILES:
                source = temporary / name
                os.chown(source, account.pw_uid, account.pw_gid)
                os.chmod(source, 0o644)
                os.replace(source, ROOT / name)
            os.chown(candidate, account.pw_uid, account.pw_gid)
            os.chmod(candidate, 0o640)
            os.replace(candidate, catalog)
            subprocess.run(['systemctl', 'start', 'capability-advisor'], check=True)
            subprocess.run(['curl', '--fail', '--silent', '--show-error', '--retry', '8', '--retry-connrefused', '--retry-delay', '1', '-H', 'Host: surfacedmp.com', 'http://127.0.0.1:8011/health'], check=True)
        result = {'status': 'deployed', 'backup': str(backup), 'lookup_count': 237, 'legacy_skus_preserved': before_count,
                  'files': {name: digest(ROOT / name) for name in FILES}, 'package_sha256': expected_sha}
        (backup / 'release.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        print(json.dumps(result, indent=2))
    except BaseException:
        if installed:
            subprocess.run(['systemctl', 'stop', 'capability-advisor'], check=False)
            for name in FILES:
                if original_files[name]:
                    shutil.copy2(backup / name, ROOT / name)
                    os.chown(ROOT / name, account.pw_uid, account.pw_gid)
                elif (ROOT / name).is_file():
                    (ROOT / name).unlink()
            shutil.copy2(backup / 'capability.sqlite3', catalog)
            os.chown(catalog, account.pw_uid, account.pw_gid)
            subprocess.run(['systemctl', 'start', 'capability-advisor'], check=False)
        raise

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
