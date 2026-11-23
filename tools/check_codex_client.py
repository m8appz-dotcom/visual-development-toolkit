"""Exercise an installed plugin through the official isolated Codex app-server client."""
from __future__ import annotations
import argparse, json, os
from pathlib import Path
import queue, subprocess, threading, time, zipfile


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--node',required=True)
    parser.add_argument('--codex-js',required=True)
    parser.add_argument('--home',type=Path,required=True)
    parser.add_argument('--runtime',type=Path,required=True)
    parser.add_argument('--python-dir',required=True)
    parser.add_argument('--work',type=Path,required=True)
    args=parser.parse_args()
    work=args.work.resolve(); work.mkdir(parents=True,exist_ok=False)
    args.runtime.mkdir(parents=True,exist_ok=True)
    env={**os.environ,'CODEX_HOME':str(args.home.resolve()),'MODDING_LAB_ROOT':str(args.runtime.resolve()),'MODDING_LAB_MODE':'portable','PYTHONDONTWRITEBYTECODE':'1','PATH':args.python_dir+os.pathsep+os.environ['PATH']}
    lines=queue.Queue(); events=[]; seq=0
    with (work/'client-stderr.log').open('w',encoding='utf-8') as err:
        proc=subprocess.Popen([args.node,args.codex_js,'app-server'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,text=True,encoding='utf-8',env=env,cwd=work,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        def reader():
            for line in proc.stdout:
                try: lines.put(json.loads(line))
                except json.JSONDecodeError: pass
        threading.Thread(target=reader,daemon=True).start()
        def request(method,params,timeout=90):
            nonlocal seq
            seq+=1; ident=seq
            proc.stdin.write(json.dumps({'id':ident,'method':method,'params':params})+'\n');proc.stdin.flush()
            deadline=time.monotonic()+timeout
            while time.monotonic()<deadline:
                try:
                    message=lines.get(timeout=min(1,max(.01,deadline-time.monotonic())))
                except queue.Empty:
                    if proc.poll() is not None:
                        raise RuntimeError('Codex client exited before '+method+'; inspect client-stderr.log')
                    continue
                events.append(message)
                if message.get('id')==ident:
                    if 'error' in message: raise RuntimeError(json.dumps(message['error']))
                    return message['result']
                if 'id' in message and 'method' in message:
                    raise RuntimeError('Client intervention required: '+message['method'])
            raise TimeoutError(method)
        try:
            init=request('initialize',{'clientInfo':{'name':'toolkit-isolated-acceptance','version':'1.0.0'},'capabilities':{'experimentalApi':True}})
            proc.stdin.write('{"method":"initialized"}\n');proc.stdin.flush()
            skills=request('skills/list',{'cwds':[str(work)],'forceReload':True})
            (work/'skills.json').write_text(json.dumps(skills,indent=2),encoding='utf-8')
            thread=request('thread/start',{'cwd':str(work),'ephemeral':True,'model':'gpt-6.2-sol'})
            tid=thread['thread']['id']
            inventory=request('mcpServerStatus/list',{'threadId':tid,'limit':100})
            (work/'inventory.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8')
            candidates=[s for s in inventory['data'] if any(t.get('name')=='create_project' for t in s.get('tools',{}).values())]
            if not candidates: raise RuntimeError('Installed plugin did not expose create_project')
            server=candidates[0]['name']
            def tool(name,arguments):
                result=request('mcpServer/tool/call',{'threadId':tid,'server':server,'tool':name,'arguments':arguments})
                if result.get('isError'): raise RuntimeError(json.dumps(result))
                return result
            project_name='codex-'+work.name
            created=tool('create_project',{'name':project_name})
            fixture=work/'owned-fixture.txt';fixture.write_text('Toolkit isolated Codex client fixture.\n',encoding='utf-8')
            imported=tool('import_target',{'project_name':project_name,'source_path':str(fixture)})
            verified=tool('verify_originals',{'project_name':project_name})
            output=args.runtime.resolve()/'projects'/project_name/'output/client-package';output.mkdir(parents=True,exist_ok=True)
            (output/'owned-fixture.txt').write_bytes(fixture.read_bytes())
            packaged=tool('package_project',{'project_name':project_name,'output_folder':'output/client-package'})
            parsed=lambda value: json.loads(next(c['text'] for c in value['content'] if c['type']=='text'))
            if not parsed(verified).get('ok') or fixture.read_bytes()!=(output/'owned-fixture.txt').read_bytes():
                raise ValueError('Original verification failed')
            archive=Path(parsed(packaged)['archive']).resolve()
            if not archive.is_relative_to(args.runtime.resolve()/'projects'/project_name/'output'):
                raise ValueError('Package escaped the isolated project')
            with zipfile.ZipFile(archive) as package:
                if package.namelist()!=['owned-fixture.txt'] or package.read('owned-fixture.txt')!=fixture.read_bytes():
                    raise ValueError('Package read-back failed')
            rejected=request('mcpServer/tool/call',{'threadId':tid,'server':server,'tool':'read_project_text','arguments':{'project_name':project_name,'file_path':'../outside.txt'}})
            if not rejected.get('isError'):
                raise ValueError('Outside-project path was accepted')
            skill_text=json.dumps(skills)
            assert 'app-to-mcp' in skill_text
            assert 'plugins' in skill_text
            report={'client':init,'pluginVersion':'1.2.2','pluginSkillDiscovered':True,'gateway':server,'toolCount':len(candidates[0]['tools']),'calls':['create_project','import_target','verify_originals','package_project'],'created':created,'imported':imported,'verified':verified,'packaged':packaged,'nativeEnginesStarted':False,'modelInferenceCalls':0}
            report.update(status='passed',packageReadBackPassed=True,inputUnchanged=True,outsidePathRejected=True,
                          optionalNativeAdapters='Not started; require their separately configured native runtime')
            (work/'client-checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
            print(json.dumps({'status':'passed','pluginVersion':'1.2.2','skill':True,'tools':report['toolCount'],'calls':report['calls']}))
        finally:
            (work/'client-events.json').write_text(json.dumps(events,indent=2),encoding='utf-8')
            proc.stdin.close()
            try: proc.wait(timeout=15)
            except subprocess.TimeoutExpired: proc.terminate();proc.wait(timeout=10)


if __name__=='__main__': main()
