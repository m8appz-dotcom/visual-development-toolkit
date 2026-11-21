from pathlib import Path
import asyncio,contextlib,hashlib,json,os,shutil,sys,zipfile
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
ROOT=Path(__file__).resolve().parents[1]
def payload(result):
    if result.isError:raise RuntimeError('MCP operation rejected')
    return result.structuredContent if result.structuredContent is not None else json.loads(next(c.text for c in result.content if c.type=='text'))
async def main():
    data=json.load(sys.stdin);directory=Path(data['directory']).resolve()
    assets=ROOT/'demo/public/assets';manifest=json.loads((assets/'manifest.json').read_text())
    allowed={a['path']:a for a in manifest};paths=list(dict.fromkeys(data['paths']))
    if any(p not in allowed for p in paths):raise ValueError('Choose a file from the committed collection')
    inputs=directory/'inputs';inputs.mkdir()
    hashes={}
    for rel in paths:
        original=(assets/rel).resolve()
        if not original.is_relative_to(assets.resolve()):raise ValueError('Invalid source path')
        digest=hashlib.sha256(original.read_bytes()).hexdigest()
        if digest!=allowed[rel]['sha256']:raise ValueError('Original changed')
        dest=inputs/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(original,dest);hashes[rel]=digest
    lab=directory/'lab';env={**os.environ,'MODDING_LAB_ROOT':str(lab),'MODDING_LAB_MODE':'docker','PYTHONDONTWRITEBYTECODE':'1'}
    async with contextlib.AsyncExitStack() as stack:
        read,write=await stack.enter_async_context(stdio_client(StdioServerParameters(command=sys.executable,args=['-B',str(ROOT/'plugins/game-modding-toolkit/server/lab_mcp.py')],env=env)))
        session=await stack.enter_async_context(ClientSession(read,write));await session.initialize()
        await session.call_tool('create_project',{'name':'demo-package'})
        payload(await session.call_tool('import_target',{'project_name':'demo-package','source_path':str(inputs)}))
        integrity=payload(await session.call_tool('verify_originals',{'project_name':'demo-package'}))
        if not integrity['ok']:raise RuntimeError('Original verification failed')
        files=[];operations=['create_project','import_target','verify_originals']
        if data['action']=='package':
            output=lab/'projects/demo-package/output/source';shutil.copytree(inputs,output)
            package=payload(await session.call_tool('package_project',{'project_name':'demo-package','output_folder':'output/source'}))
            target=directory/'toolkit-package.zip';shutil.copyfile(package['archive'],target)
            with zipfile.ZipFile(target) as z:
                if sorted(z.namelist())!=sorted(paths):raise RuntimeError('Archive contents differ')
                for rel in paths:
                    if hashlib.sha256(z.read(rel)).hexdigest()!=hashes[rel]:raise RuntimeError('Archive original differs')
            operations.append('package_project');files.append({'name':target.name,'mime':'application/zip'})
        for rel in paths:
            if hashlib.sha256((assets/rel).read_bytes()).hexdigest()!=hashes[rel]:raise RuntimeError('Committed original changed')
        result={'language':'en','transport':'MCP stdio','originalsVerified':len(paths),'archiveVerified':data['action']=='package','operations':operations,'files':[{'name':p,'sha256':hashes[p]} for p in paths]}
        target=directory/'integrity-report.json';target.write_text(json.dumps(result,indent=2),encoding='utf-8');files.append({'name':target.name,'mime':'application/json'})
        print(json.dumps({'result':result,'files':files}))
asyncio.run(main())
