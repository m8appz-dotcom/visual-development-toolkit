"""Explicit Windows runtime setup; no scenes, system preferences or unrelated config edits."""
import argparse,hashlib,json,os,shutil,subprocess,sys,time,urllib.request,venv,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert os.name=='nt','This package is verified for Windows x64'
    p=argparse.ArgumentParser();p.add_argument('--blender');p.add_argument('--archive');p.add_argument('--python-runtime');p.add_argument('--integration-home');a=p.parse_args()
    data=Path(os.environ['LOCALAPPDATA'])/'BlenderAgent';data.mkdir(parents=True,exist_ok=True)
    lock=json.loads((ROOT/'runtime/blender-lock.json').read_text(encoding='utf-8'))
    for name,digest in json.loads((ROOT/'package-hashes.json').read_text(encoding='utf-8')).items():
        path=(ROOT/name).resolve();assert path.is_relative_to(ROOT.resolve()) and sha(path)==digest,name
    blender=Path(a.blender).resolve(strict=True) if a.blender else data/'blender-5.2.1-windows-x64/blender.exe'
    if not blender.exists():
        archive=Path(a.archive).resolve(strict=True) if a.archive else data/lock['archive']
        if not archive.exists():
            temporary=archive.with_suffix('.download');urllib.request.urlretrieve(lock['url'],temporary)
            assert sha(temporary)==lock['sha256'],'Official archive hash mismatch'
            os.replace(temporary,archive)
        assert sha(archive)==lock['sha256'],'Archive hash mismatch'
        assert not blender.parent.exists(),'Partial/existing runtime requires inspection'
        stage=data/('extract-'+str(time.time_ns()));stage.mkdir()
        with zipfile.ZipFile(archive) as z:
            for item in z.infolist():
                assert (stage/item.filename).resolve().is_relative_to(stage.resolve()),'Unsafe archive member'
            z.extractall(stage)
        incoming=stage/'blender-5.2.1-windows-x64';assert (incoming/'blender.exe').is_file()
        os.rename(incoming,blender.parent)
    version=subprocess.run([str(blender),'--version'],capture_output=True,text=True,check=True,timeout=30).stdout
    assert lock['build'] in version and ('Blender '+lock['version'].split()[0]) in version,'Runtime build mismatch'
    python=Path(a.python_runtime).resolve(strict=True) if a.python_runtime else data/'venv/Scripts/python.exe'
    if not python.exists():
        venv.EnvBuilder(with_pip=True).create(data/'venv')
        subprocess.run([str(python),'-m','pip','install',*[k+'=='+v for k,v in lock['python_packages'].items()]],check=True)
    probe='import importlib.metadata as m,json;print(json.dumps({n:m.version(n) for n in '+repr(list(lock['python_packages']))+'}))'
    packages=json.loads(subprocess.check_output([str(python),'-c',probe],text=True))
    assert packages==lock['python_packages'],('Dependency version mismatch',packages)
    home=Path(a.integration_home).resolve() if a.integration_home else data/'mcp'
    home.mkdir(parents=True,exist_ok=True)
    for source,target in ((ROOT/'runtime/official-addon',home/'official-addon'),(ROOT/'runtime/blender_bootstrap.py',home/'blender_bootstrap.py')):
        if target.exists():
            if source.is_file():assert sha(source)==sha(target),'Existing bootstrap differs'
            else:
                for f in source.rglob('*'):
                    if f.is_file():assert (target/f.relative_to(source)).is_file() and sha(f)==sha(target/f.relative_to(source)),'Existing addon differs'
        elif source.is_file():shutil.copy2(source,target)
        else:shutil.copytree(source,target)
    settings={'version':'1.0.0','python':str(python),'blender':str(blender),'integration_home':str(home),'installed_from':str(ROOT),'packages':packages,'build':lock['build']}
    file=data/'settings.json'
    if file.exists():shutil.copy2(file,data/('settings-before-'+str(time.time_ns())+'.json'))
    temporary=file.with_suffix('.tmp');temporary.write_text(json.dumps(settings,indent=2),encoding='utf-8');os.replace(temporary,file)
    (data/'installation.json').write_text(json.dumps({'settings':settings,'runtime_version_output':version,'archive_sha256':lock['sha256']},indent=2),encoding='utf-8')
    print(json.dumps({'configured':True,'settings':str(file),'blender':str(blender),'integration_home':str(home)}))
if __name__=='__main__':main()
