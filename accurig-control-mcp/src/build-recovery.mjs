import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import cp from 'node:child_process';
import {Cdp} from './cdp.mjs';
import {ROOT} from './accurig.mjs';
import {inspectGlb} from './quality.mjs';
import {atomicJson,fileHash} from './integrity.mjs';
import {claimLease} from './lease.mjs';

const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
export const BUILD_WAIT_MS=90*60*1000;
export function buildEvidence(events,started){
 const fresh=events.filter(e=>e.at>=started);
 const finish=fresh.findLast(e=>e.channel==='onProgressChange'&&e.data?.processTitle===16&&e.data?.status===1);
 const glb=fresh.findLast(e=>e.channel==='onGlbConvetedInAccuRig');
 const avatar=fresh.findLast(e=>e.channel==='oniAvatarExported');
 const error=fresh.findLast(e=>e.channel==='onError');
 return {complete:!!finish&&!!glb&&glb.at>=finish.at&&!error,finish,glb,avatar,error,
  progress:fresh.findLast(e=>e.channel==='onProgressChange')};
}
export async function readBuildEvidence(core,job){
 const state=await core.main('({events:__accurigControl.events,cpu:process.cpuUsage(),pid:process.pid})');
 const evidence=buildEvidence(state.events,job.started);
 const previous=job.progress,now=Date.now();
 const changed=!previous||JSON.stringify(previous.cpu)!==JSON.stringify(state.cpu)||previous.native?.at!==evidence.progress?.at;
 job.progress={observed_at:now,native:evidence.progress??null,cpu:state.cpu,pid:state.pid,last_activity_at:changed?now:previous.last_activity_at,health:changed?'active':now-(previous.last_activity_at??now)>300000?'no_recent_activity':'waiting'};
 await core.persist(job);return evidence;
}
export async function waitForBuild(core,job,{timeoutMs=BUILD_WAIT_MS,pollMs=2000,now=Date.now,sleep=ms=>new Promise(r=>setTimeout(r,ms))}={}){
 const deadline=now()+timeoutMs;
 while(true){
  const evidence=await readBuildEvidence(core,job);
  if(evidence.error)throw Error('NATIVE_BUILD_ERROR: '+JSON.stringify(evidence.error.data));
  if(evidence.complete)return evidence;
  if(now()>=deadline)throw Error('NATIVE_COMPLETION_UNCERTAIN: build wait expired; native operation was not cancelled');
  await sleep(pollMs);
 }
}
export async function completeBuild(core,job){
 const c=job.build_context;
 if(!c||!core.model||core.revision!==job.revision||core.model.sha256!==c.model.sha256)throw Error('BUILD_CONTEXT_MISMATCH');
 if(hash(await fs.readFile(c.model.path))!==c.model.sha256)throw Error('INPUT_CHANGED');
 const evidence=await readBuildEvidence(core,job);
 if(!evidence.complete)throw Error('NATIVE_COMPLETION_UNCERTAIN: completion events not observed');
 const actor=await core.renderer("(async()=>{const id=await window.autoRig.getRiggingActorID();return (await window.api.send('getAvatarHistories')).find(h=>h.cid===id)})()");
 if(!actor?.glb||!actor.iAvatar||(c.actor_id&&actor.cid!==c.actor_id))throw Error('ACTOR_CHANGED');
 const avatar=evidence.avatar?.data?.iAvatarPath??c.expected_avatar_path;
 if(!avatar||path.resolve(actor.iAvatar)!==path.resolve(avatar)||path.dirname(path.resolve(actor.glb))!==path.dirname(path.resolve(avatar)))throw Error('AVATAR_COMPLETION_MISMATCH');
 if((await fs.stat(actor.glb)).mtimeMs<job.started)throw Error('STALE_RIG_PREVIEW');
 const structural=await inspectGlb(actor.glb);
 if(structural.verdict!=='passed')throw Error('RIG_STRUCTURE_FAILED: '+JSON.stringify(structural));
 const output=ROOT+'/data/rig-'+job.id+'.glb';
 const bytes=await fs.readFile(actor.glb);
 try{await fs.copyFile(actor.glb,output,1);}catch(e){if(e.code!=='EEXIST'||hash(await fs.readFile(output))!==hash(bytes))throw e;}
 const after=await core.snapshot();
 const preview={path:output,actor_id:actor.cid,bytes:bytes.length,sha256:hash(bytes),skins:structural.skins,joints:structural.joints};
 const receiptPath=ROOT+'/data/completion-'+job.id+'.json';
 const nativeState=await core.main('({pid:process.pid,events:__accurigControl.events})');
 const receipt={job_id:job.id,model_sha256:c.model.sha256,pid:nativeState.pid,events:nativeState.events,actor_id:actor.cid,glb_sha256:preview.sha256,avatar_sha256:await fileHash(actor.iAvatar)};
 await atomicJson(receiptPath,receipt);c.completion_receipt={path:receiptPath,sha256:await fileHash(receiptPath)};
 const result={generation_id:job.id,revision:core.revision,preview,structural,joints_before:c.joints_before,joints_after:after,completion_receipt:c.completion_receipt};
 // Persist success before enabling any export. Validation remains mandatory.
 job.result=result;job.state='completed';job.finished=Date.now();
 if(job.error){job.recovered_error=job.error;delete job.error;}
 job.reconciliation='Native completion and current actor/source verified; no regeneration';
 await core.persist(job);
 core.generation={id:job.id,completed_at:evidence.glb.at,actor_id:actor.cid,revision:core.revision,preview,joints_before:c.joints_before,joints_after:after};
 core.rigged=true;core.validation=null;core.uncertain=null;
 return result;
}
export async function processInfo(pid){
 if(!Number.isSafeInteger(pid)||pid<=0)throw Error('INVALID_PID');
 const script=`Get-CimInstance Win32_Process -Filter 'ProcessId=${pid}' | Select-Object ProcessId,ParentProcessId,ExecutablePath,CommandLine,@{n='created';e={$_.CreationDate.ToUniversalTime().ToString('o')}} | ConvertTo-Json -Compress`;
 return new Promise((resolve,reject)=>cp.execFile('powershell.exe',['-NoProfile','-NonInteractive','-Command',script],{windowsHide:true},(e,out)=>{if(e)return reject(e);try{resolve(out.trim()?JSON.parse(out):null);}catch(e){reject(e);}}));
}
export async function resumeOwnedBuild(core,id){
 if(core.cdp||core.active)throw Error('ALREADY_CONNECTED');
 if(!/^[a-f0-9]{32}$/.test(id))throw Error('INVALID_JOB_ID');
 const job=JSON.parse(await fs.readFile(ROOT+'/data/jobs/'+id+'.json','utf8')),c=job.build_context;
 if(job.type!=='build'||!['uncertain','working','interrupted','completed'].includes(job.state)||!c?.identity?.owned||!c.process_created||!c.controller_pid)throw Error('RECOVERY_CONTEXT_REQUIRED');
 const previous=await processInfo(c.controller_pid);
 if(previous&&previous.created===c.controller_created)throw Error('PREVIOUS_CONTROLLER_RUNNING');
 const actual=await processInfo(c.identity.pid);
 const expected='D:/Applications/Reallusion/AccuRIG/AccuRIG.exe';
 if(!actual)throw Error('OWNED_PROCESS_ENDED');
 if(path.resolve(actual.ExecutablePath??'').toLowerCase()!==path.resolve(expected).toLowerCase()||actual.created!==c.process_created||!actual.CommandLine.includes('--inspect-brk=127.0.0.1:'+c.identity.main_port)||!actual.CommandLine.includes('--remote-debugging-port='+c.identity.renderer_port))throw Error('OWNED_PROCESS_MISMATCH');
 if(hash(await fs.readFile(c.model.path))!==c.model.sha256)throw Error('INPUT_CHANGED');
 const targets=await (await fetch(`http://127.0.0.1:${c.identity.main_port}/json/list`)).json();
 const cdp=await Cdp.open(targets[0].webSocketDebuggerUrl);
 try{
  await cdp.send('Runtime.enable');
  let context;
  for(const e of cdp.events.filter(e=>e.method==='Runtime.executionContextCreated')){
   try{const p=await cdp.eval('typeof __accurigControl!=="undefined"?({root:__accurigControl.root,pid:process.pid,version:__accurigElectron.app.getVersion(),nonce:__accurigControl.session_nonce}):null',e.params.context.id);if(c.identity.session_nonce&&p?.nonce===c.identity.session_nonce&&p.pid===actual.ProcessId&&path.resolve(p.root)===path.resolve(ROOT)&&p.version==='2.1.1'){context=e.params.context.id;break;}}catch{}
  }
  if(!context)throw Error('OWNED_CONTEXT_NOT_FOUND');
  core.cdp=cdp;core.context=context;core.identity=c.identity;core.model=c.model;core.revision=job.revision;core.detected=true;core.registryBackup=c.registry_backup;
  core.lease=await claimLease(ROOT,c.identity);const controller=await processInfo(process.pid);c.controller_pid=process.pid;c.controller_created=controller.created;
  c.identity.controller_pid=process.pid;c.identity.controller_created=controller.created;
  await atomicJson(ROOT+'/data/session.json',c.identity);
  core.signedIn=!!await core.api('checkIsLogin',false);
  core.jobs.set(id,job);core.active=id;core.uncertain={job_id:id,type:'build',started:job.started};
  job.state='uncertain';job.resumed_at=Date.now();await core.persist(job);
  return {resumed_owned_process:true,pid:actual.ProcessId,job_id:id};
 }catch(e){cdp.close();core.cdp=null;throw e;}
}
// A completed on-disk result can be validated and previewed after Windows closes
// the owned child with its controller. This never grants native mutation/export.
export async function recoverCompletedFile(core,id){
 if(core.cdp||core.active)throw Error('ALREADY_CONNECTED');
 if(!/^[a-f0-9]{32}$/.test(id))throw Error('INVALID_JOB_ID');
 const job=JSON.parse(await fs.readFile(ROOT+'/data/jobs/'+id+'.json','utf8')),c=job.build_context;
 if(job.type!=='build'||!['uncertain','interrupted','working','completed'].includes(job.state)||!c?.completion_receipt)throw Error('COMPLETION_RECEIPT_REQUIRED');
 if(await processInfo(c.identity.pid))throw Error('APPLICATION_STILL_RUNNING');
 const previous=await processInfo(c.controller_pid);
 if(previous&&previous.created===c.controller_created)throw Error('PREVIOUS_CONTROLLER_RUNNING');
 if(hash(await fs.readFile(c.model.path))!==c.model.sha256)throw Error('INPUT_CHANGED');
 const receipt=JSON.parse(await fs.readFile(c.completion_receipt.path,'utf8'));
 if(hash(await fs.readFile(c.completion_receipt.path))!==c.completion_receipt.sha256||receipt.job_id!==id||receipt.model_sha256!==c.model.sha256||receipt.pid!==c.identity.pid)throw Error('COMPLETION_RECEIPT_MISMATCH');
 const evidence=buildEvidence(receipt.events,job.started);
 if(!evidence.complete||!evidence.avatar?.data?.iAvatarPath)throw Error('NATIVE_COMPLETION_UNCERTAIN: saved events do not certify completion');
 const avatar=path.resolve(evidence.avatar.data.iAvatarPath),folder=path.dirname(avatar);
 const base=await fs.realpath(path.join(process.env.LOCALAPPDATA,'Reallusion/ActorCore AccuRIG/File History'));
 if(path.dirname(await fs.realpath(folder))!==base)throw Error('HISTORY_PATH_MISMATCH');
 const row=await new Promise((resolve,reject)=>cp.execFile('D:/visual-development-toolkit/windows/venv/Scripts/python.exe',[ROOT+'/scripts/read_history.py',path.basename(folder)],{windowsHide:true},(e,out)=>{if(e)return reject(e);try{resolve(JSON.parse(out));}catch(e){reject(e);}}));
 if(row.folder_name!==path.basename(folder)||row.actor_id!==receipt.actor_id)throw Error('HISTORY_ACTOR_MISMATCH');
 const source=path.join(folder,'accurig.glb'),bytes=await fs.readFile(source);
 const mtime=(await fs.stat(source)).mtimeMs;
 if(mtime<job.started||mtime>evidence.glb.at+5000||hash(bytes)!==receipt.glb_sha256||hash(await fs.readFile(avatar))!==receipt.avatar_sha256)throw Error('HISTORY_CHANGED_OR_STALE');
 const structural=await inspectGlb(source);if(structural.verdict!=='passed')throw Error('RIG_STRUCTURE_FAILED');
 const output=ROOT+'/data/rig-'+id+'.glb';
 try{await fs.copyFile(source,output,1);}catch(e){if(e.code!=='EEXIST'||hash(await fs.readFile(output))!==hash(bytes))throw e;}
 const preview={path:output,actor_id:row.actor_id,bytes:bytes.length,sha256:hash(bytes),skins:structural.skins,joints:structural.joints};
 const result={generation_id:id,revision:job.revision,preview,structural,recovery_mode:'completed_history_read_only',native_app_closed:true};
 job.result=result;job.state='completed';job.finished=Date.now();job.recovered_error=job.error;delete job.error;job.reconciliation='Saved native completion, input hash, history row and file hashes verified; no regeneration';await core.persist(job);
 core.model=c.model;core.revision=job.revision;core.jobs.set(id,job);core.generation={id,revision:job.revision,actor_id:row.actor_id,completed_at:evidence.glb.at,preview};core.rigged=true;core.validation=null;core.offlineRecovery=true;core.active=null;core.uncertain=null;
 // Finish housekeeping after an interrupted close only for the same still-open
 // owned session receipt. This grants no native operations to offline recovery.
 const savedSession=await fs.readFile(ROOT+'/data/session.json','utf8').then(JSON.parse).catch(e=>{if(e.code==='ENOENT')return null;throw e;});
 if(savedSession?.session_nonce&&savedSession.session_nonce===c.identity.session_nonce&&savedSession.pid===c.identity.pid&&!savedSession.closed_at){
  const owner=await processInfo(savedSession.controller_pid);if(owner?.created===savedSession.controller_created)throw Error('PREVIOUS_CONTROLLER_RUNNING');
  core.identity=savedSession;core.registryBackup=savedSession.registry_backup;core.lease=await claimLease(ROOT,savedSession);
 }
 return {state:'idle',recovered:true,prior_job:id,result};
}
