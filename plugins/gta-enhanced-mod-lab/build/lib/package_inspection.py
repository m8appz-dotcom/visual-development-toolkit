"""Read DLC containers and source patterns without installing or executing mods."""
from __future__ import annotations
import collections,json,re,subprocess,uuid,xml.etree.ElementTree as ET
from pathlib import Path
from common import CONFIG,PLUGIN_ROOT,STATE,digest,save_json,scoped,utc
from test_runner import audit

EXPECTED={'.ydr':159,'.ydd':159,'.yft':171,'.ytd':5,'.ypt':71}

def input_folder(folder):
 source=scoped(folder,CONFIG['allowed_read_roots'])
 if not source.is_dir():raise ValueError('Package folder not found')
 paths=[]
 for p in source.rglob('*'):
  if len(paths)>=10000:raise ValueError('Package exceeds the file limit')
  if p.is_symlink() or p.is_junction():raise ValueError('Package links are not accepted')
  paths.append(p)
 if sum(p.stat().st_size for p in paths if p.is_file())>3_000_000_000:raise ValueError('Package exceeds the input size limit')
 return source,paths

def inspect_package(folder:str):
 source,paths=input_folder(folder)
 run=STATE/'runs'/uuid.uuid4().hex;run.mkdir(parents=True)
 report=run/'rpf-graph.json';output=run/'resources'
 originals={str(p.relative_to(source)):digest(p) for p in paths if p.is_file()}
 result=subprocess.run([CONFIG['dotnet'],CONFIG['package_audit_dll'],str(source),str(report),str(output)],capture_output=True,text=True,timeout=300,creationflags=subprocess.CREATE_NO_WINDOW)
 (run/'process.log').write_text(result.stdout+'\n'+result.stderr,encoding='utf-8')
 if result.returncode or not report.exists():raise RuntimeError('Package parser failed; inspect '+str(run/'process.log'))
 data=json.loads(report.read_text(encoding='utf-8'));errors=[r for r in data['files'] if r['errors']]
 resources=[r for r in data['files'] if r['resource_version'] is not None]
 versions=collections.Counter((r['extension'],r['resource_version']) for r in resources)
 generation_reviews=[{'file':r['file'],'observed':r['resource_version'],'expected_enhanced':EXPECTED[r['extension']]} for r in resources if r['extension'] in EXPECTED and r['resource_version']!=EXPECTED[r['extension']]]
 metadata=[];vehicle_models=[];handling_ids=[];content_mounts=[];text_errors=[]
 for p in output.rglob('*'):
  if p.suffix.lower() not in ('.meta','.xml') or not p.is_file():continue
  if p.stat().st_size>8_000_000:continue
  try:
   raw=p.read_bytes()
   if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():raise ValueError('XML entities rejected')
   tree=ET.fromstring(raw)
   metadata.append({'file':str(p.relative_to(output)),'root':tree.tag})
   if p.name.lower()=='vehicles.meta':
    for node in tree.findall('.//Item'):
     model=node.findtext('modelName')
     if model:vehicle_models.append({'file':str(p.relative_to(output)),'model':model,'texture':node.findtext('txdName'),'handling':node.findtext('handlingId')})
   if p.name.lower()=='handling.meta':handling_ids.extend(n.text.strip() for n in tree.findall('.//handlingName') if n.text)
   if p.name.lower()=='content.xml':content_mounts.extend({'filename':n.findtext('filename'),'type':n.findtext('fileType')} for n in tree.findall('.//dataFiles/Item'))
  except (ET.ParseError,UnicodeError,ValueError) as exc:text_errors.append({'file':str(p.relative_to(output)),'detail':str(exc)})
 maps=[r for r in data['files'] if r['extension']=='.ymap' and r['detail']]
 types=[r for r in data['files'] if r['extension']=='.ytyp' and r['detail']]
 definitions=[a for r in types for a in r['detail']['archetypes']]
 local_hashes={a['name_hash'] for a in definitions}
 external_hashes=sorted({e['archetype_hash'] for r in maps for e in r['detail']['entities']} - local_hashes)
 duplicate_hashes={str(h):n for h,n in collections.Counter(a['name_hash'] for a in definitions).items() if n>1}
 preservation=all((source/name).is_file() and digest(source/name)==sha for name,sha in originals.items())
 if not preservation:raise RuntimeError('Input files changed during package inspection')
 containers=sum(p.suffix.lower()=='.rpf' for p in paths if p.is_file())
 summary={'checked_utc':utc(),'status':'inspection_errors' if errors or data['archive_errors'] or text_errors else 'inspected' if containers else 'no_rpf_containers','input':str(source),'report':str(report),'report_sha256':digest(report),'resource_output':str(output),'rpf_containers':containers,'entries_inspected':len(data['files']),'entry_errors':len(errors),'archive_errors':data['archive_errors'],'metadata_errors':text_errors[:20],'versions':[{'extension':ext,'version':v,'count':n} for (ext,v),n in sorted(versions.items())],'gen8_resources_needing_selection_or_conversion':len(generation_reviews),'generation_reviews':generation_reviews[:30],'ymap_entities':sum(r['detail']['entity_count'] for r in maps),'archetypes':len(definitions),'mlo_rooms':sum(a['rooms'] or 0 for a in definitions),'mlo_portals':sum(a['portals'] or 0 for a in definitions),'external_archetype_hashes':external_hashes[:50],'external_archetypes_count':len(external_hashes),'external_archetypes_are_not_automatically_errors':True,'duplicate_archetype_hashes':duplicate_hashes,'duplicates_may_be_alternative_variants':True,'vehicle_models':vehicle_models,'handling_ids':sorted(set(handling_ids)),'content_mounts':content_mounts,'metadata':metadata,'originals_preserved':True,'loose_files_not_parsed_as_rpf_entries':sum(p.is_file() and p.suffix.lower() in ('.ymap','.ytyp','.ybn') for p in paths),'gameplay_tested':False,'visual_deformation_tested':False,'installation_performed':False}
 save_json(run/'package-summary.json',summary);return summary

def review_script_source(folder:str):
 """Conservative text heuristics: every finding needs human/source/runtime review."""
 source,paths=input_folder(folder);findings=[];count=0
 patterns=[
  ('wait_without_deadline',re.compile(r'while\s*\([^\n]*(?:IsLoaded|Function\.Call<bool>)[^\n]*\)'),'Review model/entity wait: require a deadline, cancellation and a failure path.'),
  ('numeric_ini_parse',re.compile(r'(?:int|float|double)\.Parse\s*\(\s*(?:Read|GetPrivateProfile)'),'Validate missing/invalid INI values with TryParse, defaults and range checks.'),
  ('p_invoke',re.compile(r'DllImport\s*\('),'P/Invoke is not itself unsafe game-memory access; inspect the exact library and call.'),
  ('forced_lod_distance',re.compile(r'LodDistance\s*=\s*(?:[5-9]\d{3}|\d{5,})'),'Large forced LOD distance needs measured CPU/GPU/streaming budgets.'),
  ('shutdown_subscription',re.compile(r'\.Aborted\s*\+='),'Verify shutdown restores cameras, controls, entities and handles on all paths.'),
  ('legacy_fivem_manifest',re.compile(r'^\s*resource_manifest_version\s',re.M),'Legacy FiveM manifest: inspect stream, data_file declarations and client behavior separately from Story Mode.'),
  ('model_hide',re.compile(r'CreateModelHide\s*\('),'Hiding a vanilla model can be needed for an interior; document scope and restoration.'),
 ]
 for p in paths:
  if not p.is_file() or p.suffix.lower() not in ('.cs','.lua'):continue
  if p.stat().st_size>2_000_000:raise ValueError('Source file exceeds review limit')
  count+=1;text=p.read_text(encoding='utf-8-sig',errors='replace')
  for code,pattern,advice in patterns:
   for m in pattern.finditer(text):
    if len(findings)>=1000:raise ValueError('Review finding limit exceeded')
    findings.append({'file':str(p.relative_to(source)),'line':text.count('\n',0,m.start())+1,'code':code,'review':advice,'confirmed_bug':False})
 run=STATE/'runs'/uuid.uuid4().hex;report=run/'source-review.json'
 value={'status':'review_required' if findings else 'no_patterns_found','files_reviewed':count,'findings':findings,'heuristics_only':True,'no_patterns_is_not_a_safety_pass':True,'gameplay_tested':False,'report':str(report)}
 save_json(report,value);return value

def field_notes():
 path=PLUGIN_ROOT/'skills/gta-enhanced-workflow/references/HALLAZGOS-PAQUETES.md'
 franchises=path.with_name('HALLAZGOS-FRANQUICIAS.md')
 starwars=path.with_name('HALLAZGOS-STARWARS-MEGAPACK.md')
 rig_qa=path.with_name('HALLAZGOS-RIG-ANIMACION-Y-QA.md')
 return {'notes':path.read_text(encoding='utf-8'),'sha256':digest(path),'franchise_notes':franchises.read_text(encoding='utf-8'),'franchise_notes_sha256':digest(franchises),'starwars_notes':starwars.read_text(encoding='utf-8'),'starwars_notes_sha256':digest(starwars),'rig_qa_notes':rig_qa.read_text(encoding='utf-8'),'rig_qa_notes_sha256':digest(rig_qa),'proprietary_files_included':False}

def rebuild_package(folder:str,converted_resources:str):
 """Build fresh DLC archive copies and validate nested payloads and logical fragments."""
 source,paths=input_folder(folder);converted,converted_paths=input_folder(converted_resources)
 if source==converted:raise ValueError('Source and converted resource folders must differ')
 if not any(p.is_file() and p.suffix.lower()=='.rpf' for p in paths):raise ValueError('No source RPF archive found')
 originals={str(p):digest(p) for p in paths+converted_paths if p.is_file()}
 run=STATE/'runs'/uuid.uuid4().hex;run.mkdir(parents=True)
 report=run/'rebuild.json';output=run/'dlc-output'
 command=[CONFIG['dotnet'],CONFIG['rpf_rebuild_dll'],str(source),str(converted),str(report),str(output)]
 result=subprocess.run(command,capture_output=True,text=True,timeout=300,creationflags=subprocess.CREATE_NO_WINDOW)
 (run/'process.log').write_text(result.stdout+'\n'+result.stderr,encoding='utf-8')
 if result.returncode or not report.exists():raise RuntimeError('DLC rebuild failed; inspect '+str(run/'process.log'))
 data=json.loads(report.read_text(encoding='utf-8'))
 package=inspect_package(str(output));readback=audit(package['resource_output'])
 if package['status']!='inspected' or readback['error_files']:raise RuntimeError('Rebuilt archive validation failed; inspect '+str(run))
 if package['gen8_resources_needing_selection_or_conversion']:raise RuntimeError('Rebuilt archive still contains Gen8 drawable/texture resources')
 if not all(Path(p).is_file() and digest(p)==sha for p,sha in originals.items()):raise RuntimeError('Input files changed during rebuild')
 summary={'status':'rebuilt_and_verified','run_id':run.name,'report':str(report),'report_sha256':digest(report),'dlc_output':str(output),'archives':[{'output':a['output'],'sha256':a['output_sha256'],'bytes':a['output_bytes'],'members_verified':a['members_verified'],'fragments_verified':len(a['fragment_preservation'])} for a in data['archives']],'converted_resources':data['converted_resources'],'package_readback':package,'asset_readback':readback,'originals_preserved':True,'converted_inputs_preserved':True,'nonresource_members_preserved':True,'gameplay_tested':False,'material_appearance_tested':False,'installation_performed':False,'scripts_converted':False}
 save_json(run/'rebuild-summary.json',summary);return summary
