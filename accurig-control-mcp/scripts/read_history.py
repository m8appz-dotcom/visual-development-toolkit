import sqlite3,pathlib,json,sys
folder=sys.argv[1]
if pathlib.Path(folder).name!=folder:raise ValueError('Invalid folder')
db=pathlib.Path.home()/'AppData/Local/Reallusion/ActorCore AccuRIG/database/actorcore.db'
c=sqlite3.connect('file:'+db.as_posix()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row
rows=c.execute('SELECT actor_id,folder_name FROM file_history WHERE folder_name=?',(folder,)).fetchall()
if len(rows)!=1:raise ValueError('History must identify exactly one actor')
print(json.dumps(dict(rows[0])))
