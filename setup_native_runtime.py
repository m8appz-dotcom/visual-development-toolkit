"""Prepare native Windows dependencies from pinned public sources and install locally."""
import json,os,pathlib,shutil,subprocess,sys
from bootstrap import ROOT,LOCK,download,sources
FLAGS=getattr(subprocess,'CREATE_NO_WINDOW',0)
ENV=os.environ.copy()
def run(argv):subprocess.run(argv,cwd=ROOT,env=ENV,check=True,creationflags=FLAGS)
if __name__=='__main__':
    if os.name!='nt':raise RuntimeError('Native mode requires Windows x64.')
    for folder in ['logs','reports','projects','temp','wheels']:(ROOT/folder).mkdir(exist_ok=True)
    ENV.update(TEMP=str(ROOT/'temp'),TMP=str(ROOT/'temp'),UV_CACHE_DIR=str(ROOT/'temp/uv'),PIP_CACHE_DIR=str(ROOT/'temp/pip'))
    uv=shutil.which('uv')
    if not uv:raise RuntimeError('Install uv from its official source first; see docs/NATIVE-WINDOWS.md.')
    managed=ROOT/'windows/python312-managed'
    run([uv,'python','install','--install-dir',str(managed),'--no-bin','--no-registry','3.12.10'])
    python=managed/'cpython-3.12.10-windows-x86_64-none/python.exe'
    if not python.is_file():raise RuntimeError('The expected private Python 3.12.10 is unavailable.')
    sources()
    records=[]
    for record in LOCK['archives']:
        if record.get('extract_to') in ['downloads/ghidra','windows/ILSpy','windows/AssetStudio','windows/dotnet-sdk']:
            download(record);records.append({k:record[k] for k in ['filename','sha256','extract_to']})
    extra=json.loads((ROOT/'native-tool-lock.json').read_text())
    for record in extra:
        download(record);records.append({k:record[k] for k in ['filename','sha256','extract_to']})
    for record in records:record['name']=record.pop('filename')
    (ROOT/'payload-lock.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
    run([str(python),'-m','ensurepip'])
    for name in ['universal-modder','ghidra-headless-mcp']:
        run([str(python),'-m','pip','wheel','--no-deps','--wheel-dir',str(ROOT/'wheels'),str(ROOT/'sources'/name)])
    run([str(python),'install_native.py','--payload',str(ROOT/'downloads')])
