from __future__ import annotations
import contextlib,hashlib,json,msvcrt,os,re,shutil,sqlite3,uuid
from datetime import datetime,timezone
from pathlib import Path

PLUGIN_ROOT=Path(__file__).resolve().parents[1]
CONFIG=json.loads((PLUGIN_ROOT/'runtime.json').read_text(encoding='utf-8'))
STATE=Path(CONFIG['state_root']);STATE.mkdir(parents=True,exist_ok=True)

def utc():return datetime.now(timezone.utc).isoformat()
def digest(path):
 with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def json_hash(value):return hashlib.sha256(canonical(value).encode()).hexdigest()
def save_json(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 tmp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
 tmp.write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8');os.replace(tmp,path)
def scoped(path,roots):
 raw=Path(path).absolute()
 for parent in [raw,*raw.parents]:
  if parent.is_symlink() or parent.is_junction():raise ValueError('Symlink/junction paths are not accepted')
 resolved=raw.resolve()
 if not any(resolved.is_relative_to(Path(root).resolve()) for root in roots):raise ValueError('Path is outside the configured scope')
 return resolved
def relative_file(value):
 value=value.replace('\\','/')
 if not value or value.startswith('/') or ':' in value or any(part in ('','..','.') for part in value.split('/')):raise ValueError('Invalid relative file path')
 return Path(value)
def valid_id(value):
 if not re.fullmatch('[0-9a-f]{32}',value):raise ValueError('Invalid operation ID')
 return value
def atomic_copy(source,destination,expected_sha):
 destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
 temp=destination.with_name('.gta-mod-lab-'+uuid.uuid4().hex+'.tmp')
 try:
  shutil.copy2(source,temp)
  if digest(temp)!=expected_sha:raise ValueError('Copy hash mismatch')
  os.replace(temp,destination)
 finally:
  if temp.exists():temp.unlink()

@contextlib.contextmanager
def ledger_lock():
 p=STATE/'ledger.lock';p.touch(exist_ok=True)
 with p.open('r+b') as f:
  if p.stat().st_size==0:f.write(b'0');f.flush()
  f.seek(0)
  try:msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
  except OSError as exc:raise RuntimeError('Another ledger operation is running') from exc
  try:yield
  finally:f.seek(0);msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1)

def db():
 conn=sqlite3.connect(STATE/'ledger.sqlite3',timeout=15)
 conn.execute('PRAGMA journal_mode=WAL')
 conn.execute('CREATE TABLE IF NOT EXISTS plans (id TEXT PRIMARY KEY, digest TEXT NOT NULL, document TEXT NOT NULL, status TEXT NOT NULL, updated TEXT NOT NULL)')
 conn.execute('CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, plan_id TEXT, action TEXT, detail TEXT, created TEXT)')
 return conn
def save_plan(document,status):
 with db() as conn:
  conn.execute('INSERT INTO plans VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET document=excluded.document,status=excluded.status,updated=excluded.updated',(document['id'],document['plan_sha256'],canonical(document),status,utc()))
def event(plan_id,action,detail):
 with db() as conn:conn.execute('INSERT INTO events(plan_id,action,detail,created) VALUES(?,?,?,?)',(plan_id,action,canonical(detail),utc()))
def load_plan(plan_id):
 with db() as conn:row=conn.execute('SELECT document,status FROM plans WHERE id=?',(valid_id(plan_id),)).fetchone()
 if not row:raise ValueError('Unknown installation plan')
 return json.loads(row[0]),row[1]
