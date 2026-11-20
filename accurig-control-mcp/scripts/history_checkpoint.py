"""Back up a single owned history row; restore only with AccuRIG closed."""
import sqlite3,pathlib,json,sys,shutil,subprocess
root=pathlib.Path('C:/Users/kenny/AppData/Local/Reallusion/ActorCore AccuRIG')
action,identifier,receipt=sys.argv[1:];receipt=pathlib.Path(receipt)
db=root/'database/actorcore.db'
if action=='backup':
 c=sqlite3.connect('file:'+db.as_posix()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row
 row=c.execute('SELECT * FROM file_history WHERE actor_id=?',(identifier,)).fetchone()
 if row is None:raise ValueError('History row absent')
 receipt.write_text(json.dumps(dict(row),indent=2),encoding='utf8')
elif action=='restore':
 running=subprocess.check_output(['tasklist','/FI','IMAGENAME eq AccuRIG.exe','/FO','CSV','/NH'],text=True)
 if '"AccuRIG.exe"' in running:raise RuntimeError('Close AccuRIG before restoring')
 row=json.loads(receipt.read_text(encoding='utf8'));assert row['actor_id']==identifier
 folder=row['folder_name'];assert pathlib.Path(folder).name==folder
 target=root/'File History'/folder;backup=receipt.parent/'files'
 if target.exists():raise RuntimeError('Target folder already exists')
 c=sqlite3.connect(db)
 if c.execute('SELECT 1 FROM file_history WHERE actor_id=? OR folder_name=?',(identifier,folder)).fetchone():raise RuntimeError('History identifier/folder already exists')
 shutil.copytree(backup,target)
 with c:c.execute('INSERT INTO file_history (actor_id,actor_name,folder_name,offset_data,created_at,updated_at) VALUES (?,?,?,?,?,?)',tuple(row[k] for k in ['actor_id','actor_name','folder_name','offset_data','created_at','updated_at']))
else:raise ValueError('Unknown action')
print(json.dumps({'operation':action,'actor_id':identifier}))
