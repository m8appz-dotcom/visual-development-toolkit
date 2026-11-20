import fs from 'node:fs/promises';
import path from 'node:path';
import {ROOT} from './accurig.mjs';
import {Cdp} from './cdp.mjs';
import {processInfo} from './build-recovery.mjs';
import {claimLease} from './lease.mjs';
import {atomicJson} from './integrity.mjs';
export async function resumeSession(core){
 if(core.cdp||core.active)throw Error('ALREADY_CONNECTED');
 const id=JSON.parse(await fs.readFile(ROOT+'/data/session.json','utf8'));
 if(!id.owned||!id.controller_pid||!id.process_created)throw Error('OWNED_SESSION_RECEIPT_REQUIRED');
 const owner=await processInfo(id.controller_pid);if(owner?.created===id.controller_created)throw Error('PREVIOUS_CONTROLLER_RUNNING');
 const app=await processInfo(id.pid);
 if(!app||app.created!==id.process_created||path.resolve(app.ExecutablePath).toLowerCase()!==path.resolve('D:/Applications/Reallusion/AccuRIG/AccuRIG.exe').toLowerCase()||!app.CommandLine.includes('--inspect-brk=127.0.0.1:'+id.main_port))throw Error('OWNED_PROCESS_MISMATCH');
 if(!id.session_nonce&&!(id.migration_authorized_at&&Date.now()-id.migration_authorized_at<3600000))throw Error('SESSION_NONCE_REQUIRED');
 const targets=await(await fetch('http://127.0.0.1:'+id.main_port+'/json/list')).json(),cdp=await Cdp.open(targets[0].webSocketDebuggerUrl);
 try{
  await cdp.send('Runtime.enable');let context;
  for(const e of cdp.events.filter(e=>e.method==='Runtime.executionContextCreated')){
   try{const s=await cdp.eval('typeof __accurigControl!=="undefined"?({pid:process.pid,root:__accurigControl.root,nonce:__accurigControl.session_nonce}):null',e.params.context.id);if(s?.pid===id.pid&&path.resolve(s.root)===path.resolve(ROOT)&&(!id.session_nonce||id.session_nonce===s.nonce)){context=e.params.context.id;break;}}catch{}
  }
  if(!context)throw Error('OWNED_CONTEXT_NOT_FOUND');
  core.cdp=cdp;core.context=context;core.identity=id;core.lease=await claimLease(ROOT,id);core.registryBackup=id.registry_backup;try{core.signedIn=!!await core.api('checkIsLogin',false);}catch{core.signedIn=false;}
  const owner=await processInfo(process.pid);id.controller_pid=process.pid;id.controller_created=owner.created;await atomicJson(ROOT+'/data/session.json',id);
  // No model or validation is inferred from the app's selection.
  return core.status();
 }catch(e){cdp.close();core.cdp=null;throw e;}
}
