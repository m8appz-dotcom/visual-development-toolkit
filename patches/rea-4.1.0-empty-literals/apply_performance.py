import pathlib,json,hashlib,difflib
B=pathlib.Path(__file__).resolve().parent;R=pathlib.Path(r'D:\visual-development-toolkit\windows\rea\node_modules\rea-agents');manifest=B/'backups/manifest.json';m=json.loads(manifest.read_text());rel='dist/application/JavaScriptSemanticGraphProjection.js';p=R/rel;raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()=='de8d40f1b3c5d676a5ac25bb9c14d070ff275771186341e9c7937c126d01ee01';assert json.loads((R/'package.json').read_text())['version']=='4.1.0';old=raw.decode();start=old.index('/** Find the innermost callable');end=old.index('/** Report extractor support');new=old[:start]+(B/'range-index-replacement.js').read_text()+old[end:]
assert not (B/'backups'/rel).exists();(B/'backups'/rel).write_bytes(raw)
out=new.encode();m['files'].append({'file':rel,'original_sha256':hashlib.sha256(raw).hexdigest(),'patched_sha256':hashlib.sha256(out).hexdigest()});manifest.write_text(json.dumps(m,indent=2));p.write_bytes(out)
(B/'performance.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+rel,tofile='b/'+rel)))
print('Range lookup patch applied with backup.')
