import hashlib,json,pathlib,shutil
BASE=pathlib.Path(__file__).resolve().parent
ROOT=pathlib.Path(r'D:\visual-development-toolkit\windows\rea\node_modules\rea-agents')
if json.loads((ROOT/'package.json').read_text())['version']!='4.1.0':raise RuntimeError('Requires REA 4.1.0; inspect a different version before patching')
EXPECTED={
 'dist/application/JavaScriptArtifactGraphContext.js':'3c30d38559a19f85e236637861fefbf970fa200f14718a1bd515d5525eca5ff7',
 'dist/application/JavaScriptArtifactGraphFindings.js':'bb017c2dc4a905439770206b33bc4e9688c78680a947447290f10fa443714548',
 'dist/application/ElectronBoundaryGraphIpc.js':'c181c9a6726b8a4f18dacfd26c94da579cddee8279565f2b62367c5be0cbb8e1',
 'dist/application/JavaScriptSemanticGraphConstruction.js':'2132da00d5cbd64383cd1885ca7f8f70ebcc5e1e0d9049b134e718582046ca93'}
CHANGES={
 'dist/application/JavaScriptSemanticGraphConstruction.js':[
 ('    label: input.label,','    // Empty source literals remain in properties; the display label is optional.\n    label: input.label === "" ? null : input.label,')],
 'dist/application/JavaScriptArtifactGraphContext.js':[
 ('    namespace,\n    key,\n});','    namespace,\n    // Reserve and escape a prefix so an empty literal cannot collide with a real key.\n    // Nonempty ordinary keys retain their existing identity.\n    key: key === "" || key.startsWith("rea-literal:")\n        ? `rea-literal:${JSON.stringify(key)}`\n        : key,\n});')],
 'dist/application/JavaScriptArtifactGraphFindings.js':[
 ('label: input.value.specifier,','label: input.value.specifier === "" ? null : input.value.specifier,'),
 ('label: input.value.value,','label: input.value.value === "" ? null : input.value.value,'),
 ('label: input.value.name ?? input.value.kind,','label: input.value.name === "" ? null : (input.value.name ?? input.value.kind),')],
 'dist/application/ElectronBoundaryGraphIpc.js':[
 ('label: finding.channel ?? finding.channel_expression,','label: finding.channel === "" ? null : (finding.channel ?? finding.channel_expression),'),
 ('label: finding.channel,','label: finding.channel === "" ? null : finding.channel,')]
}
def digest(b):return hashlib.sha256(b).hexdigest()
planned=[]
for rel,replacements in CHANGES.items():
 p=ROOT/rel;raw=p.read_bytes()
 if digest(raw)!=EXPECTED[rel]:raise RuntimeError('Unknown or already patched runtime file: '+rel)
 text=raw.decode('utf-8');newline='\r\n' if '\r\n' in text else '\n';text=text.replace('\r\n','\n')
 for old,new in replacements:
  if text.count(old)!=1:raise RuntimeError(f'Unexpected runtime content: {rel}: {old!r}')
  text=text.replace(old,new)
 planned.append((rel,raw,text.replace('\n',newline).encode('utf-8')))
if (BASE/'backups/manifest.json').exists():raise RuntimeError('Backup already exists; refusing overwrite')
manifest=[]
for rel,old,new in planned:
 backup=BASE/'backups'/rel;backup.parent.mkdir(parents=True,exist_ok=True);backup.write_bytes(old)
 manifest.append({'file':rel,'original_sha256':digest(old),'patched_sha256':digest(new)})
(BASE/'backups/manifest.json').write_text(json.dumps({'runtime':str(ROOT),'version':'4.1.0','files':manifest},indent=2))
for rel,old,new in planned:(ROOT/rel).write_bytes(new)
print(json.dumps({'patched_files':manifest},indent=2))
