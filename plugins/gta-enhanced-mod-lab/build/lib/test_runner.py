"""Repeatable static suites plus the existing, lease-controlled stock QA bridge."""
from __future__ import annotations
import argparse,asyncio,json,subprocess,tomllib,uuid
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
from common import CONFIG,PLUGIN_ROOT,STATE,digest,save_json,scoped,utc,valid_id

def audit(folder:str,convert:bool=False):
 source=scoped(folder,CONFIG['allowed_read_roots'])
 if not source.is_dir():raise ValueError('Asset folder not found')
 paths=list(source.rglob('*'))
 if len(paths)>5000:raise ValueError('Folder exceeds the audit limit')
 if any(p.is_symlink() or p.is_junction() for p in paths):raise ValueError('Symlink/junction inputs are not accepted')
 run_id=uuid.uuid4().hex;run=STATE/'runs'/run_id;run.mkdir(parents=True)
 report=run/'asset-audit.json'
 command=[CONFIG['dotnet'],CONFIG['audit_dll'],str(source),str(report)]
 output=run/'gen9'
 if convert:command.append(str(output))
 result=subprocess.run(command,capture_output=True,text=True,timeout=180,creationflags=subprocess.CREATE_NO_WINDOW)
 (run/'process.log').write_text(result.stdout+'\n'+result.stderr,encoding='utf-8')
 if result.returncode or not report.exists():raise RuntimeError('Native auditor failed; inspect '+str(run/'process.log'))
 data=json.loads(report.read_text(encoding='utf-8'))
 errors=[{'file':r['file'],'errors':r['errors']} for r in data['files'] if r['errors']]
 conversion_errors=[r for r in data.get('converted',[]) if r.get('error')]
 summary={'run_id':run_id,'checked_utc':utc(),'status':'static_errors' if errors or conversion_errors else 'static_checks_passed','files_inspected':len(data['files']),'error_files':len(errors),'warnings_files':sum(bool(r['warnings']) for r in data['files']),'errors':errors[:20],'conversion_errors':conversion_errors[:10],'report':str(report),'report_sha256':digest(report),'gen9_output':str(output) if convert else None,'gameplay_tested':False,'visual_deformation_tested':False}
 save_json(run/'summary.json',summary)
 return summary

def static_suite():
 lab=Path(CONFIG['lab_root'])
 sets={'downloaded':lab/'inputs','source':lab/'samples/spiderman/source','gen9':lab/'samples/spiderman/gen9','negative':lab/'tests/negative-fixtures'}
 results={name:audit(str(path)) for name,path in sets.items()}
 reports={name:json.loads(Path(r['report']).read_text()) for name,r in results.items()}
 failures=[]
 for name in ('downloaded','source','gen9'):
  if results[name]['error_files']:failures.append(name+' contains static errors')
 expected={'zero-weights.ydd':'Unweighted skinned vertices','bad-skin-index.ydd':'Skin indices outside bone palette','bad-triangle-index.ydd':'Triangle indices out of bounds'}
 negatives={r['file']:r for r in reports['negative']['files']}
 for filename,message in expected.items():
  if filename not in negatives or not any(message in e for e in negatives[filename]['errors']):failures.append('Negative fixture was not rejected: '+filename)
 before={r['file']:r for r in reports['source']['files']};after={r['file']:r for r in reports['gen9']['files']}
 if set(before)!=set(after):failures.append('Converted sample file set changed')
 for filename,a in before.items():
  b=after.get(filename)
  if not b:continue
  if filename.endswith(('.ydd','.yft','.ymt')) and a['detail']!=b['detail']:failures.append('Skeleton/skinning summary changed: '+filename)
  if filename.endswith('.ytd'):
   def specs(row):return [(t['Name'],t['Width'],t['Height'],t['Levels'],t['data_sha256']) for t in row['detail']['textures']]
   if specs(a)!=specs(b):failures.append('Texture payload/specification changed: '+filename)
  version={'.ydd':159,'.yft':171,'.ytd':5}.get(Path(filename).suffix)
  if version and b['resource_version']!=version:failures.append('Wrong Enhanced format: '+filename)
 run_id=uuid.uuid4().hex;report=STATE/'runs'/run_id/'static-suite.json'
 summary={'run_id':run_id,'checked_utc':utc(),'status':'failed' if failures else 'passed','files_in_downloaded_set':results['downloaded']['files_inspected'],'negative_fixtures_detected':len(expected)-sum('Negative fixture' in f for f in failures),'conversion_preservation_verified':not any('changed' in f or 'format' in f for f in failures),'failures':failures,'stages':results,'gameplay_tested':False,'visual_deformation_tested':False,'report':str(report)}
 save_json(report,summary);return summary

def result_data(result):
 if result.isError:raise RuntimeError('QA tool reported an error')
 if result.structuredContent is not None:return result.structuredContent
 for part in result.content:
  if getattr(part,'type',None)=='text':
   try:return json.loads(part.text)
   except json.JSONDecodeError:pass
 raise RuntimeError('QA result had no structured receipt')

def qa_parameters():
 config=tomllib.loads(Path(CONFIG['qa_config']).read_text(encoding='utf-8'))
 server=config.get('mcp_servers',{}).get(CONFIG['qa_server_name'])
 if not server or server.get('args')!=['-m','fivem_agent_mcp.server']:raise RuntimeError('Expected local QA bridge configuration not found')
 if not Path(server['command']).is_file():raise RuntimeError('QA bridge interpreter is missing')
 return StdioServerParameters(command=server['command'],args=server['args'],cwd=server.get('cwd'),env=server.get('env'))

async def runtime_preflight():
 try:
  async with stdio_client(qa_parameters()) as (read,write):
   async with ClientSession(read,write) as session:
    await session.initialize()
    status=result_data(await session.call_tool('qa_status',{}))
    preflight=result_data(await session.call_tool('qa_standard_preflight',{}))
  report={'checked_utc':utc(),'status':'ready' if preflight.get('allowed') else 'blocked','scope':'stock_smoke_only','preflight':preflight,'runtime_observation':{'server_http':status.get('serverHttp'),'processes':status.get('processes'),'live_connection':status.get('liveConnection')},'gameplay_tested':False}
 except Exception as exc:report={'checked_utc':utc(),'status':'blocked','reason':'qa_bridge_unavailable','detail':str(exc),'gameplay_tested':False}
 save_json(STATE/'runtime-preflight.json',report);return report

async def runtime_stock_test(case:str='stock_smoke'):
 if case not in ('observe','stock_smoke'):raise ValueError('Only existing stock QA cases are supported')
 operation_id=uuid.uuid4().hex;report_path=STATE/'runtime'/operation_id/'result.json';token_path=STATE/'runtime'/operation_id/'lease-private.json'
 async with stdio_client(qa_parameters()) as (read,write):
  async with ClientSession(read,write) as session:
   await session.initialize()
   await session.call_tool('qa_status',{})
   preflight=result_data(await session.call_tool('qa_standard_preflight',{}))
   if preflight.get('allowed') is not True:
    result={'operation_id':operation_id,'status':'blocked','preflight':preflight,'gameplay_tested':False,'report':str(report_path)}
    save_json(report_path,result);return result
   player=preflight.get('player')
   if not player or not isinstance(player.get('source'),int) or not player.get('session'):raise RuntimeError('No exact ready QA session')
   lease=result_data(await session.call_tool('qa_lease_acquire',{'owner':'gta-enhanced-mod-lab'}))
   if lease.get('ok') is not True:return {'operation_id':operation_id,'status':'blocked','reason':'qa_lease_unavailable','gameplay_tested':False}
   token=lease['leaseToken'];save_json(token_path,{'lease_token':token,'operation_id':operation_id})
   # Persist the idempotency key before dispatch; never replay uncertain actions.
   save_json(report_path,{'operation_id':operation_id,'status':'dispatching','case':case,'session':player['session'],'source':player['source']})
   try:
    receipt=result_data(await session.call_tool('qa_run_standard',{'lease_token':token,'source':player['source'],'session':player['session'],'case':case,'operation_id':operation_id}))
    await session.call_tool('qa_reconcile',{})
    observation=result_data(await session.call_tool('qa_operation',{'operation_id':operation_id}))
    release=result_data(await session.call_tool('qa_lease_release',{'lease_token':token}))
    if release.get('ok') is True:token_path.unlink()
    result={'operation_id':operation_id,'status':'passed' if receipt.get('ok') is True else 'not_passed','case':case,'receipt':receipt,'operation':observation,'lease_released':release.get('ok') is True,'gameplay_tested':case=='stock_smoke' and receipt.get('ok') is True,'report':str(report_path)}
    save_json(report_path,result);return result
   except Exception:
    save_json(report_path,{'operation_id':operation_id,'status':'outcome_unknown','gameplay_tested':False,'reconcile_required':True})
    raise

async def reconcile_runtime(operation_id:str):
 valid_id(operation_id);root=STATE/'runtime'/operation_id;token_path=root/'lease-private.json'
 if not (root/'result.json').exists():raise ValueError('Unknown runtime operation')
 async with stdio_client(qa_parameters()) as (read,write):
  async with ClientSession(read,write) as session:
   await session.initialize();await session.call_tool('qa_status',{});await session.call_tool('qa_reconcile',{})
   operation=result_data(await session.call_tool('qa_operation',{'operation_id':operation_id}));released=None
   if token_path.exists():
    token=json.loads(token_path.read_text())['lease_token'];released=result_data(await session.call_tool('qa_lease_release',{'lease_token':token})).get('ok') is True
    if released:token_path.unlink()
 result={'operation_id':operation_id,'operation':operation,'lease_released':released,'action_replayed':False};save_json(root/'reconciliation.json',result);return result

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('case',choices=['static','runtime-preflight','stock-smoke']);args=parser.parse_args()
 result=static_suite() if args.case=='static' else asyncio.run(runtime_preflight() if args.case=='runtime-preflight' else runtime_stock_test())
 print(json.dumps(result,ensure_ascii=False));return 0 if result['status'] in ('passed','ready') else 2

if __name__=='__main__':raise SystemExit(main())
