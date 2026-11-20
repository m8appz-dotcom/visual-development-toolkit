"""Send one structured request to the existing persistent real MCP test client."""
import json,pathlib,sys,time,uuid
root=pathlib.Path(__file__).resolve().parents[1];tag=sys.argv[1];request=json.loads(sys.argv[2]);identifier=request.setdefault('id',uuid.uuid4().hex)
commands=root/('reports/commands'+tag+'.jsonl');responses=root/('reports/responses'+tag+'.jsonl')
if not commands.exists():raise ValueError('Persistent MCP client has not initialized this tag')
with commands.open('a',encoding='utf-8') as f:f.write(json.dumps(request)+'\n')
for _ in range(150):
 if responses.exists():
  for line in responses.read_text(encoding='utf-8').splitlines():
   value=json.loads(line)
   if value.get('id')==identifier:
    last=root/('reports/last-'+tag+'.json');last.write_text(json.dumps(value,indent=2),encoding='utf-8');print(json.dumps(value));sys.exit(0)
 time.sleep(.2)
print(json.dumps({'pending_request':identifier,'tool':request['tool'],'do_not_replay':True}))
