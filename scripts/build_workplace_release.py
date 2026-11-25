"""Private release bundle containing code and reviewed prices, never test identities."""
import argparse,hashlib,json,os,sqlite3,sys,tempfile
from contextlib import closing
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.commercial import store


def build(output,admin_id):
    source=ROOT/'.commercial-local/commercial-public.sqlite3'
    files={str(p.relative_to(ROOT)).replace('\\','/'):p for p in (ROOT/'backend/app').rglob('*') if p.is_file() and p.suffix in ('.py','.css','.js','.html','.png') and '__pycache__' not in p.parts}
    for name in ('backend/requirements.txt','deploy/preflight_workplace.py','deploy/release_workplace.py','deploy/update_workplace.py','deploy/backup_public.py','deploy/verify_backup.py','deploy/cos_offsite_backup.py','deploy/restore_cos_backup.py'):
        files[name]=ROOT/name
    output=output.resolve();output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='workplace-release-',dir=ROOT/'artifacts') as temporary:
        seed=Path(temporary)/'commercial-seed.sqlite3'
        with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as incoming,closing(sqlite3.connect(seed)) as target:
            incoming.row_factory=sqlite3.Row
            target.executescript(store.SCHEMA)
            setting=incoming.execute('SELECT * FROM commercial_settings ORDER BY created_at DESC,id DESC LIMIT 1').fetchone()
            config=json.loads(setting['payload'])
            assert config['software_cost_factor']=='0.85','Review changed cost factor before deployment'
            policy=incoming.execute('SELECT * FROM lease_policies WHERE id=?',(config['active_policy_id'],)).fetchone()
            assert json.loads(policy['payload'])['calculation_method']=='fixed-term-v1'
            tables={'cloud_prices':list(incoming.execute("SELECT * FROM cloud_prices WHERE status='published'")),
                    'commercial_imports':list(incoming.execute('SELECT * FROM commercial_imports')),
                    'lease_policies':[policy],'commercial_settings':[setting]}
            for table,rows in tables.items():
                for row in rows:
                    values=dict(row)
                    for field in ('created_by','published_by'):
                        if field in values and values[field] is not None:values[field]=admin_id
                    columns=list(values)
                    target.execute('INSERT INTO '+table+'('+','.join(columns)+') VALUES('+','.join('?' for _ in columns)+')',list(values.values()))
            target.execute('INSERT INTO commercial_audit(occurred_at,actor,organization_id,action,target_id,details_json) VALUES(?,?,NULL,?,?,?)',(store.timestamp(),admin_id,'production.seed_prepared',config['active_policy_id'],json.dumps({'source':'reviewed local public price and policy versions','test_accounts_copied':False})))
            assert target.execute('SELECT COUNT(*) FROM cloud_prices').fetchone()[0]==14
            target.commit()
        manifest={'files':{name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in sorted(files.items())},'seed_sha256':hashlib.sha256(seed.read_bytes()).hexdigest()}
        with ZipFile(output,'w',compression=ZIP_DEFLATED) as package:
            for name,path in sorted(files.items()):package.write(path,name)
            package.write(seed,'commercial-seed.sqlite3')
            package.writestr('release-manifest.json',json.dumps(manifest,sort_keys=True))
    output.chmod(0o600)
    print(json.dumps({'archive':str(output),'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'code_files':len(files),'source_prices':14,'test_accounts':0}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--admin-id',type=int,required=True)
    args=parser.parse_args();build(args.output,args.admin_id)
