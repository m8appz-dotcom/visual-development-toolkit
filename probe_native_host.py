"""Read the installed/enabled plugin in the actual Codex host without creating a chat."""
import asyncio,json,os,pathlib,shutil,subprocess
ROOT=pathlib.Path(__file__).resolve().parent
async def main():
    cli=shutil.which('codex.cmd') or shutil.which('codex.exe')
    argv=[cli,'app-server']
    if cli.endswith('.cmd'):argv=[os.environ.get('COMSPEC','cmd.exe'),'/d','/c',*argv]
    log=(ROOT/'logs/native-codex-host-probe.log').open('w',encoding='utf-8')
    proc=await asyncio.create_subprocess_exec(*argv,cwd=ROOT,stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW,limit=32*1024*1024)
    async def send(data):proc.stdin.write((json.dumps(data)+'\n').encode());await proc.stdin.drain()
    async def request(identifier,method,params):
        await send({'id':identifier,'method':method,'params':params})
        while True:
            line=await asyncio.wait_for(proc.stdout.readline(),90)
            if not line:raise RuntimeError('Codex app server closed before responding.')
            message=json.loads(line)
            if message.get('id')==identifier:
                if 'error' in message:raise RuntimeError(str(message['error']))
                return message['result']
    def select(value):
        if isinstance(value,dict):
            if value.get('name')=='game-modding-toolkit':return [value]
            return [p for item in value.values() for p in select(item)]
        if isinstance(value,list):return [p for item in value for p in select(item)]
        return []
    try:
        await request(1,'initialize',{'clientInfo':{'name':'native-toolkit-verifier','version':'1.2.0'},'capabilities':{'experimentalApi':True}})
        await send({'method':'initialized'})
        listing=await request(2,'plugin/list',{'cwds':[str(ROOT)],'forceRefetch':False,'marketplaceKinds':['local']})
        plugins=select(listing)
        assert len(plugins)==1 and plugins[0]['installed'] and plugins[0]['enabled']
        report={'ok':True,'host':os.environ['COMPUTERNAME'],'plugins':plugins}
        (ROOT/'reports/native-codex-host-plugin.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps({'ok':True,'host':report['host'],'installed':plugins[0]['installed'],'enabled':plugins[0]['enabled'],'version':plugins[0].get('localVersion') or plugins[0].get('version')}),flush=True)
    finally:
        proc.stdin.close()
        try:await asyncio.wait_for(proc.wait(),10)
        except TimeoutError:proc.terminate();await proc.wait()
        log.close()
if __name__=='__main__':asyncio.run(main())
