"""Fetch only the pinned upstream sources and verify archive hashes."""
import hashlib,json,pathlib,subprocess,tarfile,urllib.request,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
LOCK=json.loads((ROOT/'upstream-lock.json').read_text())
FLAGS=getattr(subprocess,'CREATE_NO_WINDOW',0)
def run(args,cwd=None):subprocess.run(args,cwd=cwd,check=True,creationflags=FLAGS)
def download(record):
    folder=ROOT/record.get('save_to','downloads');folder.mkdir(parents=True,exist_ok=True)
    path=folder/record['filename']
    if not path.exists():
        partial=path.with_suffix(path.suffix+'.partial')
        request=urllib.request.Request(record['url'],headers={'User-Agent':'Visual-Development-Toolkit'})
        with urllib.request.urlopen(request,timeout=180) as response,partial.open('wb') as stream:
            while chunk:=response.read(1024*1024):stream.write(chunk)
        with partial.open('rb') as stream:sha=hashlib.file_digest(stream,'sha256').hexdigest()
        if sha!=record['sha256']:raise ValueError('Download checksum mismatch: '+record['filename'])
        partial.replace(path)
    with path.open('rb') as stream:sha=hashlib.file_digest(stream,'sha256').hexdigest()
    if sha!=record['sha256']:raise ValueError('Cached checksum mismatch: '+record['filename'])
    if 'extract_to' not in record:return
    dest=ROOT/record['extract_to'];dest.mkdir(parents=True,exist_ok=True)
    marker=dest/('.prepared-'+sha)
    if marker.exists():return
    if path.suffix=='.zip':
        with zipfile.ZipFile(path) as archive:
            for member in archive.namelist():
                if not (dest/member).resolve().is_relative_to(dest.resolve()):raise ValueError('Unsafe archive path')
            archive.extractall(dest)
    else:
        with tarfile.open(path) as archive:archive.extractall(dest,filter='data')
    if record.get('normalize_jdk'):
        candidates=[p for p in dest.iterdir() if p.is_dir() and p.name!='runtime']
        if len(candidates)!=1 or (dest/'runtime').exists():raise ValueError('Unexpected JDK extraction layout')
        source=candidates[0].resolve();target=(dest/'runtime').resolve()
        assert source.is_relative_to(dest.resolve()) and target.is_relative_to(dest.resolve())
        source.rename(target)
    marker.touch()
def sources():
    for item in LOCK['sources']:
        dest=ROOT/'sources'/item['repository'].split('/')[-1]
        if not dest.exists():
            dest.mkdir(parents=True);run(['git','init',str(dest)])
            run(['git','remote','add','origin','https://github.com/'+item['repository']+'.git'],dest)
            run(['git','fetch','--depth','1','origin',item['commit']],dest)
            run(['git','checkout','--detach',item['commit']],dest)
        head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=dest,text=True,creationflags=FLAGS).strip()
        if head!=item['commit']:raise ValueError('Existing upstream checkout differs from lock: '+str(dest))
def main():
    for name in ['downloads','windows','projects','reports','logs','sources']:(ROOT/name).mkdir(exist_ok=True)
    sources()
    for item in LOCK['archives']:
        if item.get('extract_to') in ['downloads/ghidra','windows/ILSpy','windows/AssetStudio']:download(item)
if __name__=='__main__':main()

