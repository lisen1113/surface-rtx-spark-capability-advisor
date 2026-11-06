"""Update Workplace code using a live-data clone; never replaces production databases."""
from datetime import datetime,timezone
import hashlib,json,os,pwd,shutil,sqlite3,subprocess,sys,tempfile
from pathlib import Path
from zipfile import ZipFile
from contextlib import closing

ROOT=Path('/opt/capability-advisor')


def run(command,**kwargs):return subprocess.run(command,check=True,**kwargs)


def update(archive,expected):
    archive=Path(archive).resolve()
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==expected.lower()
    env={}
    for line in Path('/etc/capability-advisor.env').read_text().splitlines():
        if line.strip() and not line.lstrip().startswith('#') and '=' in line:
            key,value=line.split('=',1);env[key]=value.strip().strip('"').strip("'")
    assert env.get('CAPABILITY_REQUIRE_AUTH')=='1' and env.get('CAPABILITY_COMMERCIAL_ENABLED')=='1'
    catalog=Path(env.get('CAPABILITY_CATALOG_PATH',str(ROOT/'data/capability.sqlite3')))
    commercial=Path(env['CAPABILITY_COMMERCIAL_PATH'])
    account=pwd.getpwnam('advisor')
    backup=ROOT/'backups'/('workplace-update-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    backup.mkdir(mode=0o700)
    run(['systemctl','start','capability-cos-backup.service'])
    with closing(sqlite3.connect(catalog.as_uri()+'?mode=ro',uri=True)) as conn:
        counts={t:conn.execute('SELECT COUNT(*) FROM '+t).fetchone()[0] for t in ('sku_lookup','imported_skus')}
    assert counts=={'sku_lookup':237,'imported_skus':11}
    with closing(sqlite3.connect(commercial)) as source,closing(sqlite3.connect(backup/'commercial.before.sqlite3')) as target:source.backup(target)
    installed=False;files={};existed={}
    try:
        with tempfile.TemporaryDirectory(prefix='.workplace-update-',dir=ROOT/'data') as temporary:
            temporary=Path(temporary);os.chown(temporary,account.pw_uid,account.pw_gid)
            shutil.copytree(ROOT/'backend/app',temporary/'backend/app',ignore=shutil.ignore_patterns('__pycache__'))
            with ZipFile(archive) as package:
                files=json.loads(package.read('release-manifest.json'))['files']
                assert all((name.startswith('backend/app/') or name.startswith('deploy/') or name=='backend/requirements.txt') and '..' not in Path(name).parts for name in files)
                for name,sha in files.items():
                    target=temporary/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(package.read(name))
                    assert hashlib.sha256(target.read_bytes()).hexdigest()==sha
                    if name.endswith('.py'):compile(target.read_text(encoding='utf-8-sig'),name,'exec')
            stage_db=temporary/'commercial.sqlite3'
            with closing(sqlite3.connect(commercial)) as source,closing(sqlite3.connect(stage_db)) as target:source.backup(target)
            os.chown(stage_db,account.pw_uid,account.pw_gid);os.chmod(stage_db,0o600)
            child={**os.environ,**env,'CAPABILITY_CATALOG_PATH':str(catalog),'CAPABILITY_COMMERCIAL_PATH':str(stage_db),'PYTHONPATH':str(temporary/'backend')}
            run(['runuser','-u','advisor','--',str(ROOT/'.venv/bin/python'),str(temporary/'deploy/preflight_workplace.py')],env=child)
            for name in files:
                target=ROOT/name;existed[name]=target.exists()
                if target.exists():destination=backup/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,destination)
            run(['systemctl','stop','capability-advisor']);installed=True
            for name in files:
                destination=ROOT/name;destination.parent.mkdir(parents=True,exist_ok=True)
                pending=destination.with_name(destination.name+'.update-new');shutil.copy2(temporary/name,pending)
                os.chown(pending,account.pw_uid,account.pw_gid);os.chmod(pending,0o644);os.replace(pending,destination)
            run(['systemctl','start','capability-advisor'])
            run(['curl','--fail','--silent','--show-error','--retry','8','--retry-connrefused','--retry-delay','1','-H','Host: surfacedmp.com','http://127.0.0.1:8011/health'])
            run(['runuser','-u','advisor','--',str(ROOT/'.venv/bin/python'),str(ROOT/'deploy/preflight_workplace.py')],env={**child,'CAPABILITY_COMMERCIAL_PATH':str(commercial),'PYTHONPATH':str(ROOT/'backend')})
            with closing(sqlite3.connect(catalog)) as conn:assert {t:conn.execute('SELECT COUNT(*) FROM '+t).fetchone()[0] for t in counts}==counts
            run(['systemctl','start','capability-cos-backup.service'])
        report={'status':'updated','backup':str(backup),'catalog_preserved':counts,'databases_replaced':False,'files':files,'files_existed':existed,'archive_sha256':expected}
        (backup/'release.json').write_text(json.dumps(report,indent=2))
        print(json.dumps({k:v for k,v in report.items() if k not in ('files','files_existed')}))
    except BaseException:
        if installed:
            subprocess.run(['systemctl','stop','capability-advisor'],check=False)
            for name in files:
                target=ROOT/name
                if existed[name]:shutil.copy2(backup/name,target);os.chown(target,account.pw_uid,account.pw_gid)
                elif target.exists():target.unlink()
            subprocess.run(['systemctl','start','capability-advisor'],check=False)
        raise


if __name__=='__main__':update(sys.argv[1],sys.argv[2])
