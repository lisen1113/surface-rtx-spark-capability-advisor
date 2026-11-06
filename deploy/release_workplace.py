"""Transactional first Workplace release; preserve live ERP and PostgreSQL identity."""
from datetime import datetime,timezone
import hashlib,json,os,pwd,shutil,sqlite3,subprocess,sys,tempfile
from pathlib import Path
from zipfile import ZipFile

ROOT=Path('/opt/capability-advisor')
ENV=Path('/etc/capability-advisor.env')
OVERRIDE=Path('/etc/systemd/system/capability-advisor.service.d/commercial.conf')
DATABASE=ROOT/'data/commercial.sqlite3'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def configuration(text):
    return {k:v.strip().strip('"').strip("'") for line in text.splitlines() if line.strip() and not line.lstrip().startswith('#') and '=' in line for k,v in [line.split('=',1)]}


def write_environment(text,values):
    lines=[line for line in text.splitlines() if not any(line.startswith(key+'=') for key in values)]
    return '\n'.join(lines+[key+'='+value for key,value in values.items()])+'\n'


def run(command,**kwargs):
    return subprocess.run(command,check=True,**kwargs)


def apply(archive,expected):
    archive=Path(archive).resolve()
    assert digest(archive)==expected.lower(),'Release archive checksum mismatch'
    assert not DATABASE.exists(),'Commercial data already exists; refusing to overwrite it'
    original_env=ENV.read_text()
    environment=configuration(original_env)
    assert environment.get('CAPABILITY_REQUIRE_AUTH')=='1' and environment.get('CAPABILITY_DEPLOYMENT_MODE')=='public'
    assert environment.get('CAPABILITY_AUTH_DATABASE_URL'),'Expected original production identity configuration'
    run(['systemctl','start','capability-cos-backup.service'])
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup=ROOT/'backups'/('workplace-release-'+stamp)
    backup.mkdir(mode=0o700)
    shutil.copy2(ENV,backup/'environment.before')
    original_override=OVERRIDE.read_bytes() if OVERRIDE.exists() else None
    with sqlite3.connect(ROOT/'data/capability.sqlite3') as source,sqlite3.connect(backup/'catalog.before.sqlite3') as target:
        source.backup(target)
        counts={name:source.execute('SELECT COUNT(*) FROM '+name).fetchone()[0] for name in ('sku_lookup','imported_skus')}
    assert counts=={'sku_lookup':237,'imported_skus':11},'Unexpected live catalog counts'
    account=pwd.getpwnam('advisor')
    installed=False
    files=[]
    existed={}
    try:
        run([str(ROOT/'.venv/bin/python'),'-m','pip','install','cryptography>=43'],stdout=subprocess.DEVNULL)
        from cryptography.fernet import Fernet
        key_path=Path('/etc/capability-commercial.key')
        key=environment.get('CAPABILITY_COMMERCIAL_KEY')
        if not key:
            if key_path.exists():
                key=key_path.read_text().strip()
            else:
                key=Fernet.generate_key().decode()
                descriptor=os.open(key_path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
                with os.fdopen(descriptor,'w') as output:output.write(key+'\n')
        Fernet(key.encode())
        new_env=write_environment(original_env,{'CAPABILITY_COMMERCIAL_ENABLED':'1','CAPABILITY_COMMERCIAL_PATH':str(DATABASE),'CAPABILITY_COMMERCIAL_KEY':key})
        child_env={**os.environ,**configuration(new_env),'CAPABILITY_CATALOG_PATH':environment.get('CAPABILITY_CATALOG_PATH',str(ROOT/'data/capability.sqlite3'))}
        with tempfile.TemporaryDirectory(prefix='.workplace-stage-',dir=ROOT/'data') as temporary:
            temporary=Path(temporary);os.chown(temporary,account.pw_uid,account.pw_gid)
            with ZipFile(archive) as package:
                manifest=json.loads(package.read('release-manifest.json'))
                files=manifest['files']
                assert files and all((name.startswith('backend/app/') or name.startswith('deploy/') or name=='backend/requirements.txt') and '..' not in Path(name).parts and not name.endswith(('.sqlite3','.key','.env')) for name in files)
                for name,sha in {**files,'commercial-seed.sqlite3':manifest['seed_sha256']}.items():
                    output=temporary/name;output.parent.mkdir(parents=True,exist_ok=True)
                    output.write_bytes(package.read(name));assert digest(output)==sha
                    os.chown(output,account.pw_uid,account.pw_gid)
                    if name.endswith('.py'):compile(output.read_text(encoding='utf-8-sig'),name,'exec')
            # The candidate seed has prices and policies only, not local accounts or customer data.
            with sqlite3.connect(temporary/'commercial-seed.sqlite3') as conn:
                for table in ('commercial_profiles','commercial_quotes','commercial_documents','azure_contracts','azure_usage','public_budget_tickets'):
                    assert conn.execute('SELECT COUNT(*) FROM '+table).fetchone()[0]==0,table
            # Add unchanged application modules to the isolated candidate tree.
            for source in (ROOT/'backend/app').rglob('*'):
                if source.is_file() and '__pycache__' not in source.parts:
                    target=temporary/source.relative_to(ROOT)
                    if not target.exists():target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
            staged={**child_env,'PYTHONPATH':str(temporary/'backend'),'CAPABILITY_COMMERCIAL_PATH':str(temporary/'commercial-seed.sqlite3')}
            run(['runuser','-u','advisor','--',str(ROOT/'.venv/bin/python'),str(temporary/'deploy/preflight_workplace.py')],env=staged)
            for name in files:
                source=ROOT/name;existed[name]=source.exists()
                if source.exists():
                    target=backup/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
            run(['systemctl','stop','capability-advisor'])
            installed=True
            for name in files:
                destination=ROOT/name;destination.parent.mkdir(parents=True,exist_ok=True)
                target=destination.with_name(destination.name+'.workplace-new')
                shutil.copy2(temporary/name,target);os.chown(target,account.pw_uid,account.pw_gid);os.chmod(target,0o644);os.replace(target,destination)
            shutil.copy2(temporary/'commercial-seed.sqlite3',DATABASE);os.chown(DATABASE,account.pw_uid,account.pw_gid);os.chmod(DATABASE,0o600)
            ENV.write_text(new_env);os.chmod(ENV,0o600)
            OVERRIDE.parent.mkdir(parents=True,exist_ok=True)
            OVERRIDE.write_text('[Service]\nReadWritePaths=/opt/capability-advisor/data\nUMask=0077\n')
            run(['systemctl','daemon-reload']);run(['systemctl','start','capability-advisor'])
            run(['curl','--fail','--silent','--show-error','--retry','8','--retry-connrefused','--retry-delay','1','-H','Host: surfacedmp.com','http://127.0.0.1:8011/health'])
            run(['runuser','-u','advisor','--',str(ROOT/'.venv/bin/python'),str(ROOT/'deploy/preflight_workplace.py')],env={**child_env,'PYTHONPATH':str(ROOT/'backend')})
            with sqlite3.connect(ROOT/'data/capability.sqlite3') as conn:
                assert {name:conn.execute('SELECT COUNT(*) FROM '+name).fetchone()[0] for name in counts}==counts
            run(['systemctl','start','capability-cos-backup.service'])
        result={'status':'deployed','backup':str(backup),'catalog_preserved':counts,'identity_preserved':True,'files':files,'archive_sha256':expected}
        (backup/'release.json').write_text(json.dumps(result,indent=2))
        print(json.dumps({'status':result['status'],'backup':str(backup),'catalog_preserved':counts,'identity_preserved':True,'code_files':len(files),'archive_sha256':expected}))
    except BaseException:
        if installed:
            subprocess.run(['systemctl','stop','capability-advisor'],check=False)
            for name in files:
                destination=ROOT/name
                if existed.get(name):shutil.copy2(backup/name,destination);os.chown(destination,account.pw_uid,account.pw_gid)
                elif destination.exists():destination.unlink()
            if DATABASE.exists():shutil.move(DATABASE,backup/'commercial.failed.sqlite3')
            shutil.copy2(backup/'environment.before',ENV)
            if original_override is None:OVERRIDE.unlink(missing_ok=True)
            else:OVERRIDE.write_bytes(original_override)
            subprocess.run(['systemctl','daemon-reload'],check=False);subprocess.run(['systemctl','start','capability-advisor'],check=False)
        raise


if __name__=='__main__':apply(sys.argv[1],sys.argv[2])
