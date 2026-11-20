from pathlib import Path
import json,sqlite3,hashlib
root=Path(__file__).resolve().parents[1]
job_path=root/'data/jobs/16e56003518f4a57b8208d2150b91d39.json'
job=json.loads(job_path.read_text(encoding='utf-8-sig'));ctx=job['build_context']
status=json.loads((root/'reports/nico-recovery-live-status.json').read_text(encoding='utf-8'))['result']
avatar=Path(ctx['expected_avatar_path']);glb=avatar.parent/'accurig.glb'
db=Path.home()/'AppData/Local/Reallusion/ActorCore AccuRIG/database/actorcore.db'
c=sqlite3.connect('file:'+db.as_posix()+'?mode=ro',uri=True)
rows=c.execute('SELECT actor_id FROM file_history WHERE folder_name=?',(avatar.parent.name,)).fetchall()
assert len(rows)==1
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(Path(ctx['model']['path']))==ctx['model']['sha256']
receipt={'job_id':job['id'],'model_sha256':ctx['model']['sha256'],'pid':status['pid'],'events':status['events'],'actor_id':rows[0][0],'glb_sha256':sha(glb),'avatar_sha256':sha(avatar),'provenance':'Native status captured by accurig_status after completion; file and read-only history binding during explicit controller migration'}
p=root/'reports/nico-completion-receipt.json'
p.write_text(json.dumps(receipt,indent=2),encoding='utf-8')
ctx['completion_receipt']={'path':str(p),'sha256':sha(p)}
job_path.write_text(json.dumps(job,indent=2),encoding='utf-8')
print(json.dumps({'receipt':str(p),'actor_id':rows[0][0],'glb_bytes':glb.stat().st_size}))
