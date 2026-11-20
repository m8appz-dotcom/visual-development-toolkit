import {Workflow as Previous} from './workflow-v02.mjs';
import {ROOT} from './accurig.mjs';
import {inspectJoints,assertJointReview,jointHash} from './joints-quality.mjs';
import {atomicJson,digest,fileHash,manifest,verifyManifest,assertReadback,publishExclusive} from './integrity.mjs';
import {claimLease,assertLease,releaseLease} from './lease.mjs';
import {processInfo} from './build-recovery.mjs';
import {resumeSession} from './session-recovery.mjs';
import {stopOwnedApplication} from './shutdown.mjs';
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import cp from 'node:child_process';
const all=j=>[...(j.bodyJoints??[]),...(j.fingerJoints??[])];
const delay=ms=>new Promise(r=>setTimeout(r,ms));
const run=(file,args)=>new Promise((resolve,reject)=>cp.execFile(file,args,{windowsHide:true},(e,out)=>e?reject(e):resolve(out)));
const PY='D:/visual-development-toolkit/windows/venv/Scripts/python.exe';
export class Workflow extends Previous{
 constructor(){super();this.resetSession();}
 resetSession(){this.model=null;this.rigged=false;this.generation=null;this.validation=null;this.calibration=null;this.jointReview=null;this.visualReview=null;this.detected=false;this.offlineRecovery=false;this.fingerConfig={fingers:'None',finger_count:0};}
 invalidate(){super.invalidate();this.jointReview=null;this.visualReview=null;}
 async connect({resume_owned_session=false}={}){if(this.cdp)return this.status();if(this.active||this.uncertain)throw Error('BUSY_OR_UNCERTAIN');this.resetSession();if(resume_owned_session)return resumeSession(this);try{const result=await super.connect();this.lease=await claimLease(ROOT,this.identity);return {...result,lease_owner:this.lease.pid};}catch(e){if(this.cdp&&this.identity?.owned){try{this.lease??=await claimLease(ROOT,this.identity);await this.close();}catch(cleanup){throw Error(e.message+'; owned startup cleanup failed: '+cleanup.message);}}throw e;}}
 async persist(job){try{await atomicJson(ROOT+'/data/jobs/'+job.id+'.json',job);}catch(e){throw Error('STATE_PERSISTENCE_FAILED: '+e.message);}}
 async checkLease(){return assertLease(this.lease);}
 async api(channel,value){if(!['getJointsInfo','checkIsLogin'].includes(channel)){const j=this.jobs.get(this.active);if(j&&!j.native_started){j.native_started=true;await this.persist(j);}}return super.api(channel,value);}
 async job(type,operation){
  this.guard(type==='validate'&&this.offlineRecovery);
  if(!this.offlineRecovery)await this.checkLease();
  const job={id:crypto.randomUUID().replaceAll('-',''),type,state:'working',phase:type,started:Date.now(),revision:this.revision};
  this.active=job.id;this.jobs.set(job.id,job);
  try{await this.persist(job);}catch(e){if(this.active===job.id)this.active=null;this.jobs.delete(job.id);throw e;}
  Promise.resolve().then(()=>operation(job)).then(async result=>{
   if(type==='build'||type==='calibrate')await this.bindGeneration();
   job.result=result;job.state='completed';job.finished=Date.now();await this.persist(job);
   if(this.active===job.id)this.active=null;
  }).catch(async error=>{
   job.error=error.message;job.finished=Date.now();
   if(['build','calibrate'].includes(type)){this.generation=null;this.rigged=false;this.validation=null;this.visualReview=null;}
   const uncertain=type!=='validate'&&(/timed out|Inspector disconnected|NATIVE_COMPLETION_UNCERTAIN|PERSISTENCE_AFTER_NATIVE/i.test(error.message)||(job.native_started&&/STATE_PERSISTENCE_FAILED/.test(error.message)));
   job.state=uncertain?'uncertain':'failed';
   if(uncertain)this.uncertain={job_id:job.id,type,started:job.started};else if(this.active===job.id)this.active=null;
   try{await this.persist(job);}catch(e){job.persistence_error=e.message;this.uncertain={job_id:job.id,type,started:job.started,reason:'STATE_PERSISTENCE_FAILED'};this.active=job.id;}
  });return {...job};
 }
 async inspect(){const j=await this.joints();return {...j,...inspectJoints(j.data,this.fingerConfig),model:this.model,review:this.jointReview};}
 async detect(options={}){this.fingerConfig={fingers:options.fingers??'Both',finger_count:options.finger_count??5};return super.detect(options);}
 async reviewJoints({expected_revision,joints_sha256,verdict,views,observations,resolved_warnings=[]}){
  this.guard();if(this.revision!==expected_revision)throw Error('REVISION_CONFLICT');
  const data=await this.snapshot(),q=inspectJoints(data,this.fingerConfig);
  if(q.joints_sha256!==joints_sha256)throw Error('JOINTS_CHANGED');
  const required=['front','left','right','back',...(this.fingerConfig.fingers==='None'?[]:['hands'])];
  if(required.some(v=>!views.includes(v))||!observations?.trim())throw Error('MULTIVIEW_REVIEW_REQUIRED');
  if(verdict==='accepted'&&(q.errors.length||q.warnings.some(w=>!resolved_warnings.includes(w.code))))throw Error('UNRESOLVED_JOINT_ANATOMY: '+JSON.stringify(q.errors.length?q.errors:q.warnings));
  this.jointReview={revision:this.revision,model_sha256:this.model.sha256,joints_sha256,verdict,views,observations,resolved_warnings,reviewed_at:Date.now()};
  await atomicJson(ROOT+'/reports/joints-review-'+joints_sha256+'.json',this.jointReview);return this.jointReview;
 }
 async build(){this.guard();const q=inspectJoints(await this.snapshot(),this.fingerConfig);assertJointReview(this.jointReview,q,this.model,this.revision);return super.build();}
 async edit(args){
  this.guard();if(args.expected_revision!==this.revision)throw Error('REVISION_CONFLICT');if(args.coordinate_space!=='accurig_native_model')throw Error('COORDINATE_SPACE_REQUIRED');
  const changes=args.changes;if(!changes?.length||new Set(changes.map(c=>c.name)).size!==changes.length)throw Error('EMPTY_OR_DUPLICATE_EDIT');
  const before=await this.snapshot(),list=all(before),byName=new Map(list.map(j=>[j.name,j]));
  for(const c of changes){if(!byName.has(c.name))throw Error('UNKNOWN_JOINT: '+c.name);for(const v of [c.position,c.rotation].filter(Boolean))if(!Object.values(v).every(Number.isFinite))throw Error('NONFINITE_EDIT');if(c.rotation&&Math.abs(Math.hypot(...Object.values(c.rotation))-1)>.002)throw Error('QUATERNION_MUST_BE_NORMALIZED');if(!c.position&&!c.rotation&&c.masked===undefined)throw Error('EMPTY_JOINT_EDIT');}
  const checkpoint=await this.checkpoint();this.invalidate();
  return this.job('edit',async()=>{
   try{await this.apply(changes);const after=await this.snapshot();for(const c of changes)assertReadback(c,all(after).find(j=>j.name===c.name));this.detected=true;return {revision:this.revision,checkpoint_id:checkpoint.id,before:changes.map(c=>byName.get(c.name)),after:changes.map(c=>all(after).find(j=>j.name===c.name))};}
   catch(e){if(/timed out|Inspector disconnected/.test(e.message))throw e;try{const rollback=changes.map(c=>byName.get(c.name));await this.apply(rollback);const got=all(await this.snapshot());for(const c of rollback)assertReadback(c,got.find(j=>j.name===c.name));}catch(r){throw Error('NATIVE_COMPLETION_UNCERTAIN: rollback not verified: '+r.message);}throw e;}
  });
 }
 async bindGeneration(){
  const g=this.generation;if(!g)throw Error('GENERATION_NOT_COMPLETED');
  const row=await this.currentActor();if(row.cid!==g.actor_id)throw Error('ACTOR_CHANGED');
  g.binding={model_sha256:this.model.sha256,preview_sha256:await fileHash(g.preview.path),avatar_path:row.iAvatar,avatar_sha256:await fileHash(row.iAvatar),actor_id:row.cid};
  const job=this.jobs.get(g.id);if(job){job.generation=g;await this.persist(job);}
  await atomicJson(ROOT+'/data/generation-'+g.id+'.json',g);
 }
 async currentActor(){const row=await this.renderer("(async()=>{const id=await window.autoRig.getRiggingActorID();return (await window.api.send('getAvatarHistories')).find(h=>h.cid===id)})()");if(!row)throw Error('CURRENT_ACTOR_NOT_FOUND');return row;}
 async assertGeneration({native=false,visual=false}={}){
  const g=this.generation;if(!g||g.revision!==this.revision||!g.preview?.path||!this.model?.path)throw Error('NO_CURRENT_GENERATION');
  if(await fileHash(g.preview.path)!==g.preview.sha256||await fileHash(this.model.path)!==this.model.sha256)throw Error('GENERATION_ARTIFACT_CHANGED');
  if(native){await assertLease(this.lease);const row=await this.currentActor();if(!g.binding||row.cid!==g.actor_id||g.binding.actor_id!==row.cid||path.resolve(row.iAvatar)!==path.resolve(g.binding.avatar_path)||await fileHash(row.iAvatar)!==g.binding.avatar_sha256)throw Error('ACTOR_OR_AVATAR_CHANGED');if(this.calibration?.generation_id===g.id&&await fileHash(this.calibration.avatar)!==this.calibration.avatar_sha256)throw Error('CALIBRATED_AVATAR_CHANGED');}
  if(visual){if(this.visualReview?.generation_id!==g.id||this.visualReview.preview_sha256!==g.preview.sha256||this.visualReview.verdict!=='accepted')throw Error('VISUAL_REVIEW_REQUIRED');if(this.validation?.generation_id!==g.id||this.validation.preview_sha256!==g.preview.sha256||this.validation.structure!=='passed'||this.validation.deformation==='failed')throw Error('VALIDATE_CURRENT_GENERATION_FIRST');if(!this.validation.report||!this.validation.report_sha256||this.visualReview.report_sha256!==this.validation.report_sha256||await fileHash(this.validation.report)!==this.validation.report_sha256)throw Error('REVIEWED_VALIDATION_REPORT_CHANGED');}
  return g;
 }
 async validate(){this.guard(this.offlineRecovery);const g=await this.assertGeneration();return this.job('validate',async()=>{
  const report=ROOT+'/reports/quality-'+g.id+'.json';await this.runBlender(g.preview.path,report);const q=JSON.parse(await fs.readFile(report));await this.assertGeneration();
  this.validation={generation_id:g.id,revision:this.revision,preview_sha256:g.preview.sha256,structure:q.structure,deformation:q.deformation,visual:'pending',ready_for_delivery:false,verdict:q.verdict,report,report_sha256:await fileHash(report)};this.visualReview=null;await atomicJson(ROOT+'/data/validation-'+g.id+'.json',this.validation);return {...this.validation,quality:q};
 });}
 async recordVisual({generation_id,preview_sha256,verdict,views,poses,observations,open_defects=[]}){
  this.guard(this.offlineRecovery);const g=await this.assertGeneration();if(g.id!==generation_id||g.preview.sha256!==preview_sha256)throw Error('REVIEW_ARTIFACT_CHANGED');
  const v=this.validation;if(!v||v.generation_id!==g.id||await fileHash(v.report)!==v.report_sha256)throw Error('VALIDATION_REQUIRED');
  const q=JSON.parse(await fs.readFile(v.report)),required=['front','left','right','back','hands'];
  if(!views.length||!poses.length||!observations?.trim()||poses.some(name=>!q.poses.some(p=>p.name===name)))throw Error('INVALID_VISUAL_OBSERVATION');
  if(verdict==='accepted'&&(required.some(x=>!views.includes(x))||q.poses.some(p=>!poses.includes(p.name))))throw Error('INCOMPLETE_VISUAL_COVERAGE');
  if(verdict==='accepted'&&(v.structure!=='passed'||v.deformation==='failed'||open_defects.length))throw Error('OPEN_QUALITY_DEFECTS');
  this.visualReview={generation_id,preview_sha256,report_sha256:v.report_sha256,verdict,views,poses,observations,open_defects,reviewed_at:Date.now()};v.visual=verdict;v.ready_for_delivery=verdict==='accepted'&&v.structure==='passed'&&v.deformation!=='failed';
  await atomicJson(ROOT+'/reports/visual-'+g.id+'.json',this.visualReview);await atomicJson(ROOT+'/data/validation-'+g.id+'.json',v);return {...v,review:this.visualReview};
 }
 async calibrate(args){await this.assertGeneration({native:true});return super.calibrate(args);}
 async reconcile(args={}){const r=await super.reconcile(args);if(r.recovered){if(this.active===r.prior_job)this.active=null;if(this.cdp)await this.bindGeneration();}return r;}
 async export(output,{target='blender',mode='MeshOnly',avatar='original'}={}){
  this.guard();const g=await this.assertGeneration({native:true,visual:true});if(avatar!=='original'&&(!this.calibration||this.calibration.generation_id!==g.id))throw Error('CALIBRATED_AVATAR_NOT_CURRENT');
  output=path.resolve(output);if(!output.toLowerCase().endsWith('.fbx'))throw Error('FBX_REQUIRED');const glb=output.replace(/\.fbx$/i,'.glb');
  for(const p of [output,glb,output+'.receipt.json']){try{await fs.access(p);throw Error('OUTPUT_EXISTS: '+p);}catch(e){if(e.code!=='ENOENT')throw e;}}
  await fs.mkdir(path.dirname(output),{recursive:true});const lock=output+'.accurig-lock';const reservation=await fs.open(lock,'wx');await reservation.close();
  try{return await this.job('export',async job=>{
   const stage=ROOT+'/outputs/staging/'+job.id;await fs.mkdir(stage,{recursive:true});const fbx=stage+'/character.fbx';
   try{
    await this.assertGeneration({native:true,visual:true});if(!await this.api('checkIsLogin',false))throw Error('AUTH_REQUIRED');
    const source=avatar==='calibrated'?this.calibration.avatar:g.binding.avatar_path;
    const temp=await this.main("__accurigRequire('path').join(__accurigElectron.app.getPath('userData'),'Temp File')");await fs.mkdir(temp,{recursive:true});if((await fs.readdir(temp)).length)throw Error('EXPORT_TEMP_PROTECTION');
    job.native_started=true;await this.persist(job);await this.main(`(()=>{const d=__accurigElectron.dialog;__accurigControl.originalSaveDialog=d.showSaveDialog;d.showSaveDialog=async(...a)=>a.at(-1)?.title==='Export FBX'?{canceled:false,filePath:${JSON.stringify(fbx)}}:__accurigControl.originalSaveDialog.apply(d,a);})()`);
    try{await this.renderer(`(async()=>{await window.converter.setFileType('fbx');await window.converter.setTarget(${JSON.stringify(target)});await window.converter.setMeshMotionMode(${JSON.stringify(mode)});await window.converter.setEmbedTexture(true);await window.converter.exportFBX(${JSON.stringify(source)},null,false);})()`,240000);}
    finally{await this.main('if(__accurigControl.originalSaveDialog){__accurigElectron.dialog.showSaveDialog=__accurigControl.originalSaveDialog;delete __accurigControl.originalSaveDialog;}true');}
    const bytes=await fs.readFile(fbx);if(!bytes.subarray(0,23).equals(Buffer.from('Kaydara FBX Binary  \x00\x1a\x00')))throw Error('INVALID_FBX_HEADER');
    await this.assertGeneration({native:true,visual:true});const report=stage+'/reimport.json';await this.runBlender(fbx,report);const quality=JSON.parse(await fs.readFile(report));
    const original=JSON.parse(await fs.readFile(this.validation.report));if(quality.structure!=='passed'||quality.deformation==='failed'||JSON.stringify(quality.deform_bones)!==JSON.stringify(original.deform_bones)||quality.meshes.reduce((n,m)=>n+m.triangles,0)!==original.meshes.reduce((n,m)=>n+m.triangles,0))throw Error('EXPORTED_FBX_MISMATCH_OR_QUALITY_FAILED');
    await publishExclusive([[fbx,output],[g.preview.path,glb]],output+'.receipt.json');
    return {generation_id:g.id,target,mode,avatar,fbx:{path:output,sha256:await fileHash(output)},preview:{path:glb,sha256:await fileHash(glb)},quality_report:report,ready_for_delivery:true};
   }catch(e){await atomicJson(stage+'/REJECTED.json',{error:e.message,generation_id:g.id});throw e;}finally{await fs.unlink(lock).catch(()=>{});}
  });}catch(e){await fs.unlink(lock).catch(()=>{});throw e;}
 }
 async archiveGeneration(id){
  this.guard();await this.checkLease();const prior=await this.jobStatus(id),p=prior.result?.preview;
  if(prior.state!=='completed'||!['build','calibrate'].includes(prior.type)||!p?.actor_id)throw Error('OWNED_COMPLETED_GENERATION_REQUIRED');
  if(this.generation?.actor_id===p.actor_id)throw Error('ACTIVE_HISTORY');
  const row=await this.renderer(`(async()=>{return(await window.api.send('getAvatarHistories')).find(h=>h.cid===${JSON.stringify(p.actor_id)})})()`);
  if(!row||await fileHash(row.glb)!==p.sha256)throw Error('HISTORY_CHANGED');
  const folder=await fs.realpath(path.dirname(row.glb)),base=await fs.realpath(path.join(process.env.LOCALAPPDATA,'Reallusion/ActorCore AccuRIG/File History'));
  if(path.dirname(folder)!==base||path.basename(folder)!==row.folder)throw Error('HISTORY_PATH_MISMATCH');
  const backup=ROOT+'/backups/history-'+id+'-'+Date.now(),items=await manifest(folder);await fs.mkdir(backup,{recursive:true});await fs.cp(folder,backup+'/files',{recursive:true,errorOnExist:true,force:false});await verifyManifest(backup+'/files',items);
  await run(PY,[ROOT+'/scripts/history_checkpoint.py','backup',row.cid,backup+'/row.json']);const saved=JSON.parse(await fs.readFile(backup+'/row.json'));if(saved.actor_id!==row.cid||saved.folder_name!==row.folder)throw Error('HISTORY_ROW_BACKUP_MISMATCH');
  await atomicJson(backup+'/manifest.json',items);await this.renderer(`window.api.send('removeAvatarHistory',${JSON.stringify(row.folder)})`);
  return {archived_actor:row.cid,backup,verified_files:items.length,receipt:backup+'/row.json',restore_command:[PY,ROOT+'/scripts/history_checkpoint.py','restore',row.cid,backup+'/row.json']};
 }
 async deleteGeneration({generation_id,confirm_generation_id,extra_paths=[]}){
  this.guard();await assertLease(this.lease);if(generation_id!==confirm_generation_id)throw Error('EXPLICIT_GENERATION_CONFIRMATION_REQUIRED');
  const j=await this.jobStatus(generation_id),p=j.result?.preview;if(j.state!=='completed'||!p?.actor_id||this.generation?.actor_id===p.actor_id)throw Error('OWNED_INACTIVE_GENERATION_REQUIRED');
  const row=await this.renderer(`(async()=>{return(await window.api.send('getAvatarHistories')).find(h=>h.cid===${JSON.stringify(p.actor_id)})})()`);if(!row||await fileHash(row.glb)!==p.sha256)throw Error('HISTORY_CHANGED');
  const base=await fs.realpath(path.join(process.env.LOCALAPPDATA,'Reallusion/ActorCore AccuRIG/File History')),folder=await fs.realpath(path.dirname(row.glb));if(path.dirname(folder)!==base||path.basename(folder)!==row.folder)throw Error('HISTORY_PATH_MISMATCH');
  const paths=[p.path,...extra_paths],copies=[];
  for(const item of paths){try{const real=await fs.realpath(item);if(!real.toLowerCase().endsWith('.glb')||await fileHash(real)!==p.sha256)throw Error('DELETE_COPY_IDENTITY_MISMATCH');copies.push(real);}catch(e){if(e.code!=='ENOENT')throw e;}}
  const items=await manifest(folder);const receipt={generation_id,actor_id:row.cid,folder,files:items,copies,authorized_action:'delete exact last generation',started:Date.now()};await atomicJson(ROOT+'/reports/deleted-'+generation_id+'.json',receipt);
  await this.renderer(`window.api.send('removeAvatarHistory',${JSON.stringify(row.folder)})`);if(await fs.stat(folder).then(()=>true,()=>false))throw Error('NATIVE_HISTORY_DELETE_NOT_CONFIRMED');
  for(const item of copies)await fs.unlink(item);receipt.finished=Date.now();receipt.freed_bytes=items.reduce((n,x)=>n+x.bytes,0)+copies.length*p.bytes;await atomicJson(ROOT+'/reports/deleted-'+generation_id+'.json',receipt);j.state='deleted';j.deleted_receipt=ROOT+'/reports/deleted-'+generation_id+'.json';await this.persist(j);return receipt;
 }
 async prepareImportWorkspace(){
  this.guard();await this.checkLease();if(this.model?.prepared)throw Error('LOADED_MODEL_REQUIRES_NEW_SESSION');
  const folder=await this.main("__accurigRequire('path').join(__accurigElectron.app.getPath('userData'),'fbxToObjTemp')");
  const expected=path.join(process.env.LOCALAPPDATA,'Reallusion/ActorCore AccuRIG/fbxToObjTemp');if(path.resolve(folder)!==path.resolve(expected))throw Error('IMPORT_TEMP_PATH_MISMATCH');
  await fs.mkdir(folder,{recursive:true});const items=await manifest(folder);if(!items.length)return {prepared:true,existing_files:0};
  const stamp=Date.now(),backup=ROOT+'/backups/import-temp-'+stamp;await fs.mkdir(backup,{recursive:true});await fs.cp(folder,backup+'/files',{recursive:true,errorOnExist:true,force:false});await verifyManifest(backup+'/files',items);
  // C: -> D: cannot rename atomically. Isolate on the source volume only after
  // the complete cross-volume copy is verified, then recreate the SDK workspace.
  const isolated=folder+'.isolated-'+stamp;await fs.rename(folder,isolated);
  try{await verifyManifest(isolated,items);await fs.mkdir(folder);await atomicJson(backup+'/receipt.json',{original:folder,files:items,operation:'preserve-and-isolate-before-native-import'});if(path.dirname(await fs.realpath(isolated))!==path.dirname(path.resolve(expected))||path.basename(isolated)!==path.basename(expected)+'.isolated-'+stamp)throw Error('ISOLATED_TEMP_PATH_MISMATCH');await fs.rm(isolated,{recursive:true});}
  catch(e){if(!await fs.stat(folder).then(()=>true,()=>false))await fs.rename(isolated,folder);throw e;}
  return {prepared:true,existing_files:items.length,backup,receipt:backup+'/receipt.json'};
 }
 async close({recover_owned_session=false}={}){
  if(this.active||this.uncertain)throw Error('BUSY_OR_UNCERTAIN');
  if(recover_owned_session&&!this.cdp&&!this.identity){
   const id=JSON.parse(await fs.readFile(ROOT+'/data/session.json','utf8'));
   if(!id.owned||!id.session_nonce||id.closed_at||!id.registry_backup)throw Error('OWNED_UNCLOSED_SESSION_REQUIRED');
   const prior=await processInfo(id.controller_pid);if(prior?.created===id.controller_created)throw Error('PREVIOUS_CONTROLLER_RUNNING');
   for(const name of await fs.readdir(ROOT+'/data/jobs')){if(!name.endsWith('.json'))continue;const j=JSON.parse(await fs.readFile(ROOT+'/data/jobs/'+name,'utf8'));if(j.build_context?.identity?.pid===id.pid&&['working','uncertain','interrupted'].includes(j.state))throw Error('UNRESOLVED_NATIVE_BUILD');}
   this.lease=await claimLease(ROOT,id);this.identity=id;this.registryBackup=id.registry_backup;
  }
  if(this.cdp||this.identity?.owned){await this.checkLease();const id=this.identity,backup=this.registryBackup;
   const verifyOwned=async()=>{const p=await processInfo(id.pid);if(p&&(p.created!==id.process_created||path.resolve(p.ExecutablePath??'').toLowerCase()!==path.resolve(id.executable).toLowerCase()))throw Error('OWNED_PROCESS_MISMATCH');return p;};
   const shutdown=await stopOwnedApplication({requestQuit:async()=>{if(this.cdp&&await verifyOwned())await this.main('setTimeout(()=>__accurigElectron.app.quit(),100);true');},disconnect:()=>{this.cdp?.close();this.cdp=null;},isRunning:async()=>!!await verifyOwned(),forceTerminate:async()=>{await this.checkLease();if(await verifyOwned())process.kill(id.pid);}});
   if(backup){await run(PY,[ROOT+'/registry_state.py','restore',backup]);const after=ROOT+'/data/registry-verified-'+Date.now()+'.json';await run(PY,[ROOT+'/registry_state.py','backup',after]);if(digest(JSON.stringify(JSON.parse(await fs.readFile(after))))!==digest(JSON.stringify(JSON.parse(await fs.readFile(backup)))))throw Error('PREFERENCES_RESTORE_NOT_VERIFIED');}
   await atomicJson(ROOT+'/data/session.json',{...id,closed_at:Date.now(),preferences_restored:!!backup,...shutdown});await releaseLease(this.lease);this.lease=null;this.resetSession();this.identity=null;this.registryBackup=null;this.revision++;return {closed_owned_session:true,preferences_restored:!!backup,...shutdown};
  }
  this.resetSession();return {closed_owned_session:false,preferences_restored:false,no_native_session:true};
 }
}
