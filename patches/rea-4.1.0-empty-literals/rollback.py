import pathlib,json,hashlib
BASE=pathlib.Path(__file__).resolve().parent
manifest=json.loads((BASE/'backups/manifest.json').read_text())
root=pathlib.Path(manifest['runtime'])
for row in manifest['files']:
 current=(root/row['file']).read_bytes()
 if hashlib.sha256(current).hexdigest()!=row['patched_sha256']:
  raise RuntimeError('Runtime changed; refusing overwrite: '+row['file'])
for row in manifest['files']:
 if row['original_sha256'] is None:continue
 original=(BASE/'backups'/row['file']).read_bytes()
 if hashlib.sha256(original).hexdigest()!=row['original_sha256']:raise RuntimeError('Backup mismatch')
for row in manifest['files']:
 if row['original_sha256'] is None:(root/row['file']).unlink()
 else:(root/row['file']).write_bytes((BASE/'backups'/row['file']).read_bytes())
print('Restored original REA 4.1.0 runtime files.')
