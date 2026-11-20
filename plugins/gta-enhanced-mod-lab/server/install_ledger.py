"""Scoped, journaled installation/rollback. Defaults only permit our staging area."""
from __future__ import annotations
import hashlib,shutil,uuid
from pathlib import Path
from common import CONFIG,STATE,atomic_copy,canonical,digest,event,json_hash,ledger_lock,load_plan,relative_file,save_plan,scoped,utc

MAX_FILES=1000
def plan_install(source_folder:str,target_folder:str,relative_paths:list[str]):
 source=scoped(source_folder,CONFIG['allowed_read_roots']);target=scoped(target_folder,CONFIG['allowed_install_roots'])
 if not source.is_dir():raise ValueError('Source directory not found')
 if not relative_paths or len(relative_paths)>MAX_FILES:raise ValueError('Select 1 to 1000 files')
 entries=[];seen=set();total=0
 for name in relative_paths:
  rel=relative_file(name);key=str(rel).casefold()
  if key in seen:raise ValueError('Duplicate target path')
  seen.add(key)
  src=scoped(source/rel,[source]);dst=scoped(target/rel,[target])
  if not src.is_file() or (dst.exists() and not dst.is_file()):raise ValueError('Expected regular source/target file')
  if src==dst:raise ValueError('Source and target must differ')
  if src.suffix.lower() in ('.exe','.bat','.cmd','.ps1'):raise ValueError('Executable/script installers are not copied by this ledger')
  if src.name.casefold()=='objectspawnunlocknbuild.asi':raise ValueError('This plugin is flagged by the author as potentially incompatible with Enhanced; a verified port must be reviewed separately')
  total+=src.stat().st_size
  if total>1024**3:raise ValueError('Plan exceeds the 1 GiB limit')
  expected={'.ydd':159,'.ydr':159,'.yft':171,'.ytd':5,'.ypt':71}.get(src.suffix.lower())
  if expected:
   with src.open('rb') as stream:header=stream.read(8)
   if header[:4]!=b'RSC7' or int.from_bytes(header[4:8],'little')!=expected:raise ValueError('Resource is not in the required Enhanced format: '+str(rel))
  entries.append({'relative_path':str(rel),'source':str(src),'target':str(dst),'source_sha256':digest(src),'before_sha256':digest(dst) if dst.exists() else None,'bytes':src.stat().st_size,'state':'pending'})
 body={'id':uuid.uuid4().hex,'created_utc':utc(),'source_root':str(source),'target_root':str(target),'files':entries}
 body['plan_sha256']=json_hash(body)
 with ledger_lock():save_plan(body,'planned');event(body['id'],'planned',{'files':len(entries),'target':str(target)})
 return {'plan_id':body['id'],'plan_sha256':body['plan_sha256'],'status':'planned','target_root':str(target),'files':[{'relative_path':r['relative_path'],'bytes':r['bytes'],'replaces_existing':r['before_sha256'] is not None} for r in entries]}

def paths(document):
 source=scoped(document['source_root'],CONFIG['allowed_read_roots']);target=scoped(document['target_root'],CONFIG['allowed_install_roots'])
 for row in document['files']:
  rel=relative_file(row['relative_path']);src=scoped(source/rel,[source]);dst=scoped(target/rel,[target])
  if str(src)!=row['source'] or str(dst)!=row['target']:raise ValueError('Journal path mismatch')
  yield row,src,dst

def apply_install(plan_id:str,expected_plan_sha256:str):
 with ledger_lock():
  document,status=load_plan(plan_id)
  if document['plan_sha256']!=expected_plan_sha256:raise ValueError('Review digest does not match the plan')
  if status=='applied':return {'plan_id':plan_id,'status':'applied','idempotent':True}
  if status!='planned':raise ValueError('Plan is not fresh; inspect or rollback its existing state')
  items=list(paths(document))
  for row,src,dst in items:
   if not src.exists() or digest(src)!=row['source_sha256']:raise ValueError('Source changed since review')
   current=digest(dst) if dst.exists() else None
   if current!=row['before_sha256']:raise ValueError('Target changed since review; prepare a new plan')
  backup_root=scoped(STATE/'backups'/plan_id,[STATE]);backup_root.mkdir(parents=True,exist_ok=True)
  try:
   for i,(row,src,dst) in enumerate(items):
    if row['before_sha256'] is not None:
     backup=backup_root/(str(i)+'.original')
     if backup.exists() and digest(backup)!=row['before_sha256']:raise ValueError('Existing backup does not match original')
     if not backup.exists():shutil.copy2(dst,backup)
     if digest(backup)!=row['before_sha256']:raise ValueError('Backup hash mismatch')
     row['backup']=str(backup)
    row['state']='prepared';save_plan(document,'applying')
   for row,src,dst in items:
    if (digest(dst) if dst.exists() else None)!=row['before_sha256']:raise ValueError('Target changed while preparing backups')
    atomic_copy(src,dst,row['source_sha256']);row['state']='applied';save_plan(document,'applying')
   save_plan(document,'applied');event(plan_id,'applied',{'files':len(items)})
   return {'plan_id':plan_id,'status':'applied','files_verified':len(items),'backup_root':str(backup_root)}
  except Exception as exc:
   save_plan(document,'failed');event(plan_id,'failed',{'reason':str(exc),'rollback_available':True});raise

def rollback_install(plan_id:str):
 with ledger_lock():
  document,status=load_plan(plan_id)
  if status=='rolled_back':return {'plan_id':plan_id,'status':'rolled_back','idempotent':True}
  if status=='planned':raise ValueError('This plan has not been applied')
  items=list(paths(document));work=[]
  for row,src,dst in items:
   current=digest(dst) if dst.exists() else None
   if current==row['before_sha256']:continue
   if current!=row['source_sha256']:raise ValueError('Target has independent changes; rollback refuses to overwrite them')
   backup=None
   if row['before_sha256'] is not None:
    backup=scoped(row.get('backup',''),[STATE/'backups'/plan_id])
    if not backup.is_file() or digest(backup)!=row['before_sha256']:raise ValueError('Original backup is missing or changed')
   work.append((row,dst,backup))
  save_plan(document,'rolling_back')
  for row,dst,backup in reversed(work):
   # Resolve and verify immediately before the replacement or removal.
   scoped(dst,CONFIG['allowed_install_roots'])
   if not dst.exists() or digest(dst)!=row['source_sha256']:raise ValueError('Target changed during rollback')
   if backup is not None:atomic_copy(backup,dst,row['before_sha256'])
   else:dst.unlink()
   row['state']='restored';save_plan(document,'rolling_back')
  save_plan(document,'rolled_back');event(plan_id,'rolled_back',{'files_restored':len(work)})
  return {'plan_id':plan_id,'status':'rolled_back','files_restored':len(work),'backups_preserved':True}

def list_plans():
 from common import db
 with db() as conn:rows=conn.execute('SELECT id,digest,status,updated FROM plans ORDER BY updated DESC LIMIT 50').fetchall()
 return {'plans':[{'plan_id':r[0],'plan_sha256':r[1],'status':r[2],'updated_utc':r[3]} for r in rows]}
