"""Local Windows MCP gateway. Analysis runs in the dedicated Docker container."""
from __future__ import annotations
import hashlib,json,os,pathlib,re,shutil,subprocess,sys,time,zipfile
from mcp.server.fastmcp import FastMCP

ROOT=pathlib.Path(os.environ.get('MODDING_LAB_ROOT',r'D:\modding-lab')).resolve()
PROJECTS=ROOT/'projects'
os.environ.setdefault('UM_KB',str(ROOT/'sources/universal-modder/knowledge'))
CONTAINER='modding-lab-analysis'
MCP=FastMCP('Visual Development Toolkit')
FLAGS=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
NATIVE=os.environ.get('MODDING_LAB_MODE')=='native'
if NATIVE and os.name=='nt':FLAGS|=subprocess.BELOW_NORMAL_PRIORITY_CLASS

def run(argv:list[str],timeout:int=180,cwd=None)->dict:
    proc=subprocess.run(argv,cwd=cwd,stdin=subprocess.DEVNULL,text=True,encoding='utf-8',errors='replace',capture_output=True,timeout=timeout,creationflags=FLAGS)
    result={'ok':proc.returncode==0,'exit_code':proc.returncode,'stdout':proc.stdout[-100000:],'stderr':proc.stderr[-12000:]}
    try:result['data']=json.loads(proc.stdout)
    except ValueError:pass
    return result

def project(name:str)->pathlib.Path:
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}',name):raise ValueError('Use a project name containing lowercase letters, numbers and hyphens.')
    path=(PROJECTS/name).resolve()
    if path.parent!=PROJECTS.resolve() or not path.is_dir():raise ValueError('Create the project first.')
    return path

def contained(base:pathlib.Path,relative:str)->pathlib.Path:
    if not relative or pathlib.Path(relative).is_absolute():raise ValueError('Use a relative path inside the project.')
    path=(base/relative).resolve()
    if not path.is_relative_to(base.resolve()):raise ValueError('Path leaves the project.')
    return path

def linux(path:pathlib.Path)->str:
    if NATIVE:return str(path.resolve())
    return '/lab/projects/'+path.resolve().relative_to(PROJECTS.resolve()).as_posix()

def docker(argv:list[str],timeout:int=180,cwd='/lab/projects')->dict:
    if NATIVE:
        config=json.loads((ROOT/'native-runtime.json').read_text())
        commands={
            'um':[str(ROOT/'windows/venv/Scripts/um.exe')],
            'rea':[config['node'],str(ROOT/'windows/rea/node_modules/rea-agents/scripts/rea.mjs')],
            'ilspycmd':[str(ROOT/'windows/dotnet-sdk/dotnet.exe'),str(next((ROOT/'windows/ilspy-tools').rglob('ilspycmd.dll')))],
            'python3':[sys.executable],
        }
        if argv[0] not in commands:raise ValueError('Unsupported native component.')
        return run([*commands[argv[0]],*argv[1:]],timeout,PROJECTS if cwd=='/lab/projects' else cwd)
    extra=['-e','UM_KB=/opt/universal-modder/knowledge']
    if argv[:2]==['um','fal'] and os.environ.get('FAL_KEY'):extra+=['-e','FAL_KEY']
    return run(['docker','exec',*extra,'-w',cwd,CONTAINER,'timeout',str(timeout),*argv],timeout+15)

def save_result(base:pathlib.Path,name:str,result:dict):
    path=base/'reports'/f'{name}-{time.time_ns()}.json'
    path.write_text(json.dumps(result,indent=2),encoding='utf-8')
    result['report']=str(path)
    return result

@MCP.tool()
def component_status()->dict:
    """Check the actual Docker engine and all installed analysis and Windows components."""
    if NATIVE:
        import importlib.metadata as metadata
        config=json.loads((ROOT/'native-runtime.json').read_text())
        props=dict(line.split('=',1) for line in (pathlib.Path(config['ghidra'])/'Ghidra/application.properties').read_text().splitlines() if '=' in line)
        return {'host':os.environ.get('COMPUTERNAME'),'runtime_root':str(ROOT),'mode':'native','windows':{name:(ROOT/'windows'/name).is_dir() for name in ['ILSpy','AssetStudio','AssetBridge','venv']},'fal_key_available':bool(os.environ.get('FAL_KEY')),'blender_available':bool(shutil.which('blender')),'analysis':{'ok':True,'versions':{'ghidra':props['application.version'],'headless_mcp':metadata.version('ghidra-headless-mcp'),'universal_modder':metadata.version('universal-modder'),'rea':docker(['rea','--version'],30),'ilspycmd':docker(['ilspycmd','--version'],30),'java':run([str(pathlib.Path(config['java'])/'bin/java.exe'),'-version'],30)},'rea_native_boundary':'Experimental Windows x64 native PE read-only P0; other targets depend on the selected REA provider.'}}
    state=run(['docker','inspect',CONTAINER,'--format','{{json .State}}'],30)
    status={'host':os.environ.get('COMPUTERNAME'),'runtime_root':str(ROOT),'container':state,'windows':{name:(ROOT/'windows'/name).is_dir() for name in ['ILSpy','AssetStudio','AssetBridge','venv']},'fal_key_available':bool(os.environ.get('FAL_KEY')),'blender_available':bool(shutil.which('blender'))}
    if state['ok']:
        status['analysis']=docker(['python3','-c',"import json,subprocess,pathlib,importlib.metadata as m; props=dict(line.split('=',1) for line in pathlib.Path('/opt/ghidra/Ghidra/application.properties').read_text().splitlines() if '=' in line); print(json.dumps({'ghidra':props['application.version'],'headless_mcp':m.version('ghidra-headless-mcp'),'universal_modder':m.version('universal-modder'),'rea':subprocess.check_output(['rea','--version'],text=True).strip(),'ilspycmd':subprocess.check_output(['ilspycmd','--version'],text=True).strip(),'node':subprocess.check_output(['node','--version'],text=True).strip(),'java':subprocess.run(['java','-version'],capture_output=True,text=True).stderr.strip()}))"],60)
    return status

@MCP.tool()
def create_project(name:str)->dict:
    """Create an isolated project with input, output, reports and backups folders."""
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}',name):raise ValueError('Invalid project name.')
    path=PROJECTS/name
    if path.exists():raise ValueError('Project already exists; choose another name or reuse it.')
    for folder in ['input','output','reports','backups']:(path/folder).mkdir(parents=True,exist_ok=True)
    (path/'project.json').write_text(json.dumps({'name':name,'created':time.time(),'originals_modified':False},indent=2))
    return {'project':name,'windows_path':str(path),'docker_path':linux(path)}

@MCP.tool()
def import_target(project_name:str,source_path:str)->dict:
    """Copy a caller-selected file or folder into project input and record hashes. Originals remain untouched."""
    base=project(project_name);source=pathlib.Path(source_path).resolve(strict=True)
    if source==ROOT or ROOT.is_relative_to(source):raise ValueError('Choose a target, not the lab installation or its parent.')
    dest=base/'input'/source.name
    if dest.exists():raise ValueError('An input with that name already exists.')
    entries=list(source.rglob('*')) if source.is_dir() else [source]
    if any(p.is_symlink() or p.is_junction() or not p.resolve().is_relative_to(source if source.is_dir() else source.parent) for p in entries):raise ValueError('Targets containing links are not supported.')
    files=[p for p in entries if p.is_file()]
    if source.is_dir():shutil.copytree(source,dest)
    else:shutil.copy2(source,dest)
    manifest=[]
    for item in files:
        with item.open('rb') as stream:sha=hashlib.file_digest(stream,'sha256').hexdigest()
        manifest.append({'path':str(item),'bytes':item.stat().st_size,'sha256':sha})
    (base/'reports'/f'import-{source.name}.json').write_text(json.dumps(manifest,indent=2))
    return {'input_path':str(dest),'docker_path':linux(dest),'files':len(files),'manifest':manifest[:20]}

@MCP.tool()
def recon_game(game_path:str)->dict:
    """Inspect a caller-selected Windows game folder with universal-modder without launching it."""
    path=pathlib.Path(game_path).resolve(strict=True)
    return run([str(ROOT/'windows/venv/Scripts/um.exe'),'scan',str(path)],180)

@MCP.tool()
def run_um(project_name:str,args:list[str],platform:str='docker')->dict:
    """Run universal-modder's scan, sprite, video, backup, render3d, comfy, fal, kb or publish check CLI in a project. Use --help to discover exact flags. Outputs must stay in the project. Cloud generation requires the user's key and authorized cost."""
    base=project(project_name)
    if not args or args[0] not in ['scan','sprite','video','backup','render3d','comfy','fal','kb','publish','--help']:raise ValueError('Unsupported group. Use the separate Windows interaction tool for win.')
    if args[0]=='publish' and args[1:2]!=['check']:raise ValueError('Only package checking is exposed; publishing requires a separate workflow.')
    if args[0]=='kb' and args[1:2] in [['pr'],['sync']]:raise ValueError('Network mutations are not exposed by this tool.')
    for arg in args:
        value=arg.split('=',1)[-1]
        if '..' in pathlib.PurePath(value).parts or re.match(r'^[A-Za-z]:',value) or value.startswith(('/','\\')):raise ValueError('Use project-relative paths.')
    if platform=='docker':
        # The gateway returns Windows artifact paths; map relative Windows separators for Linux.
        mapped=[arg.replace('\\','/') if not NATIVE and arg.startswith(('input\\','output\\','reports\\','backups\\')) else arg for arg in args]
        result=docker(['um',*mapped],180,linux(base))
    elif platform=='windows':result=run([str(ROOT/'windows/venv/Scripts/um.exe'),*args],180,base)
    else:raise ValueError('Platform must be docker or windows.')
    return save_result(base,'um',result)

@MCP.tool()
def rea_command(project_name:str,args:list[str])->dict:
    """Run REA analysis commands inside Docker. Paths refer to /lab/projects/PROJECT. Full REA MCP tools are also connected separately."""
    base=project(project_name)
    allowed=['--help','--version','doctor','providers','capabilities','analyze','analyze-javascript-application','decompile','function','functions','strings','info','inspect-managed-artifact','compare']
    if not args or args[0] not in allowed:raise ValueError('Use an analysis command or --help.')
    for arg in args:
        if arg.startswith('/') and not arg.startswith(linux(base)+'/'):raise ValueError('Absolute paths must belong to this project.')
        if '..' in pathlib.PurePosixPath(arg).parts:raise ValueError('Path traversal is not allowed.')
    return save_result(base,'rea',docker(['rea',*args],240,linux(base)))

@MCP.tool()
def decompile_dotnet(project_name:str,input_file:str,type_name:str='')->dict:
    """Decompile a managed assembly into C# with the real ILSpy command-line engine."""
    base=project(project_name);source=contained(base,input_file)
    if not source.is_file():raise ValueError('Assembly not found.')
    out=base/'output'/('ilspy-'+str(time.time_ns()));out.mkdir()
    argv=['ilspycmd','-o',linux(out)]
    if type_name:argv+=['-t',type_name]
    else:argv+=['-p']
    result=docker([*argv,linux(source)],180)
    result['output_path']=str(out)
    result['files']=[str(p.relative_to(base)) for p in out.rglob('*') if p.is_file()]
    return save_result(base,'ilspy',result)

def assets(project_name,input_path,mode,asset_type='all'):
    base=project(project_name);source=contained(base,input_path)
    out=base/'output'/('assets-'+str(time.time_ns()))
    argv=[str(ROOT/'windows/AssetBridge/publish/AssetBridge.exe'),mode,str(source)]
    if mode=='export':argv += [str(out),asset_type]
    result=run(argv,180,cwd=ROOT/'windows/AssetBridge/publish')
    if mode=='export':
        result['output_path']=str(out)
        if 'data' in result:result['ok']=result['ok'] and not any(i.get('error') for i in result['data']['items'])
    return save_result(base,'assetstudio',result)

@MCP.tool()
def inspect_unity_assets(project_name:str,input_path:str)->dict:
    """Inventory Unity assets with the original Windows AssetStudio libraries. Supported upstream versions: Unity 3.4â€“2022.1."""
    return assets(project_name,input_path,'inspect')

@MCP.tool()
def export_unity_assets(project_name:str,input_path:str,asset_type:str='all')->dict:
    """Export Unity textures/sprites to PNG, text, audio, meshes to OBJ and other objects to dumps. FBX animation export remains available in the installed AssetStudio GUI."""
    return assets(project_name,input_path,'export',asset_type)

@MCP.tool()
def list_project_files(project_name:str,folder:str='output')->dict:
    """List project artifacts, their sizes and relative paths."""
    base=project(project_name);root=contained(base,folder)
    items=[{'path':str(p.relative_to(base)),'bytes':p.stat().st_size} for p in root.rglob('*') if p.is_file()]
    return {'files':items[:500],'total_files':len(items)}

@MCP.tool()
def read_project_text(project_name:str,file_path:str,max_chars:int=20000)->dict:
    """Read a bounded UTF-8 source or report file from a project."""
    base=project(project_name);path=contained(base,file_path)
    with path.open('r',encoding='utf-8',errors='replace') as stream:text=stream.read(min(max(max_chars,1),100000)+1)
    return {'path':str(path),'text':text[:max_chars],'truncated':len(text)>max_chars}

@MCP.tool()
def verify_originals(project_name:str)->dict:
    """Compare imported originals against the hashes saved at import time."""
    base=project(project_name);results=[]
    for report in (base/'reports').glob('import-*.json'):
        for record in json.loads(report.read_text()):
            path=pathlib.Path(record['path'])
            sha=hashlib.file_digest(path.open('rb'),'sha256').hexdigest() if path.is_file() else None
            results.append({'path':str(path),'unchanged':sha==record['sha256']})
    return {'ok':bool(results) and all(i['unchanged'] for i in results),'files':results}

@MCP.tool()
def windows_game_tool(project_name:str,args:list[str],visible_interaction_authorized:bool=False)->dict:
    """Use universal-modder's native Windows game tools. Launch, capture, input and recording require explicit human authorization for visible interaction. kill and registry edits are excluded."""
    base=project(project_name)
    if not args or args[0] not in ['--help','ps','shot','record','drive','launch']:raise ValueError('Unsupported Windows operation.')
    if args[0] not in ['--help','ps'] and not visible_interaction_authorized:raise ValueError('Obtain explicit user authorization for this visible game interaction first.')
    return save_result(base,'windows',run([str(ROOT/'windows/venv/Scripts/um.exe'),'win',*args],180,base))

@MCP.tool()
def open_windows_tool(tool:str,visible_interaction_authorized:bool=False)->dict:
    """Open the installed ILSpy or original AssetStudio GUI when the human explicitly requests that visible window. AssetStudio retains its native FBX and animation export functions."""
    if not visible_interaction_authorized:raise ValueError('Obtain explicit user authorization to open this visible window.')
    executables={'ilspy':ROOT/'windows/ILSpy/ILSpy.exe','assetstudio':ROOT/'windows/AssetStudio/AssetStudioGUI.exe'}
    if tool not in executables:raise ValueError('Choose ilspy or assetstudio.')
    path=executables[tool]
    env=os.environ.copy()
    if tool=='assetstudio':env['DOTNET_ROLL_FORWARD']='Major'
    process=subprocess.Popen([str(path)],cwd=path.parent,env=env,creationflags=FLAGS,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    return {'started':True,'pid':process.pid,'executable':str(path),'gui_verified':False}

@MCP.tool()
def package_mod(project_name:str,output_folder:str)->dict:
    """Optional legacy mod packaging, only for an explicit mod request. For game/app source or assets use package_project."""
    base=project(project_name);folder=contained(base,output_folder)
    if not folder.is_relative_to(base/'output'):raise ValueError('Package an authored folder inside output.')
    check=docker(['um','publish','check',linux(folder)],60)
    if not check['ok']:return check
    archive=base/'output'/f'mod-{time.time_ns()}.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in folder.rglob('*'):
            if p.is_file():z.write(p,p.relative_to(folder))
    return {'ok':True,'archive':str(archive),'check':check}

@MCP.tool()
def package_project(project_name:str,output_folder:str)->dict:
    """Bundle authored game/app source and visual assets from a project output folder into a ZIP. Does not build an installer or publish anything."""
    base=project(project_name);folder=contained(base,output_folder)
    if not folder.is_dir() or not folder.is_relative_to(base/'output') or folder==base/'output':
        raise ValueError('Choose an authored subfolder inside output.')
    entries=list(folder.rglob('*'))
    if any(p.is_symlink() or p.is_junction() or not p.resolve().is_relative_to(folder) for p in entries):
        raise ValueError('Package folders containing links are not supported.')
    files=[p for p in entries if p.is_file()]
    if not files:raise ValueError('The selected output folder has no files.')
    archive=base/'output'/f'project-{time.time_ns()}.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in files:z.write(p,p.relative_to(folder).as_posix())
    return {'ok':True,'archive':str(archive),'files':len(files),'kind':'source-and-assets'}

if __name__=='__main__':MCP.run(transport='stdio')
