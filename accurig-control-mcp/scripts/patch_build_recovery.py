from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=root/'src/workflow.mjs'
s=p.read_text(encoding='utf-8')
s=s.replace("import {inspectGlb} from './quality.mjs';", "import {inspectGlb} from './quality.mjs';\nimport {waitForBuild,completeBuild,resumeOwnedBuild,processInfo} from './build-recovery.mjs';")
start=s.index(' async build(){')
end=s.index('\n async rig(',start)
s=s[:start]+''' async build(){
  this.guard();if(!this.model?.prepared)throw Error('MODEL_NOT_PREPARED');
  await this.historyGuard();this.rigged=false;this.generation=null;this.validation=null;this.calibration=null;
  return this.job('build',async job=>{
   const before=await this.snapshot(),actor=await this.renderer('window.autoRig.getRiggingActorID()');
   const app=await processInfo(this.identity.pid),controller=await processInfo(process.pid);
   job.build_context={model:{...this.model},actor_id:actor,joints_before:before,identity:{...this.identity},process_created:app.created,controller_pid:process.pid,controller_created:controller.created,registry_backup:this.registryBackup};
   job.phase='skinning_current_joints';await this.persist(job);
   await this.main('__accurigControl.events=[];true');await this.api('characterize',false);
   await waitForBuild(this,job);return completeBuild(this,job);
  });
 }'''+s[end:]
start=s.index(' async reconcile(){')
end=s.index('\n async close(){',start)
s=s[:start]+''' async reconcile({recovery_job_id}={}){
  if(recovery_job_id&&!this.cdp)await resumeOwnedBuild(this,recovery_job_id);
  if(!this.uncertain)return {state:'idle',action:'none'};
  const u=this.uncertain;
  if(u.type==='build'){
   const j=this.jobs.get(u.job_id);
   if(!j?.build_context)return {state:'uncertain',action:'recovery context required; no mutation permitted',operation:u};
   try{const result=await completeBuild(this,j);return {state:'idle',recovered:true,prior_job:j.id,result};}
   catch(error){j.recovery_error=error.message;await this.persist(j);return {state:'uncertain',action:'wait or inspect recovery error; no mutation permitted',operation:u,error:error.message};}
  }
  const done=await this.main(`__accurigControl.events.some(e=>e.at>=${u.started}&&e.channel==='onProgressChange'&&e.data?.processTitle===${u.type==='export'?4:u.type==='detect'?3:-1}&&e.data?.status===1)`);
  if(!done)return {state:'uncertain',action:'wait; no mutation permitted',operation:u};
  const j=this.jobs.get(u.job_id);j.state='interrupted';j.reconciliation='Native completion observed; prior result invalidated. Inspect before starting a new operation.';await this.persist(j);this.active=null;this.uncertain=null;this.rigged=false;this.generation=null;return {state:'idle',prior_job:j.id,result_invalidated:true};
 }'''+s[end:]
p.write_text(s,encoding='utf-8')
p=root/'src/server.mjs';s=p.read_text(encoding='utf-8')
s=s.replace("['accurig_reconcile_session','Reconcile an uncertain native operation without replay. Never assumes a timeout cancelled the SDK.',{},()=>core.reconcile(),false]", "['accurig_reconcile_session','Recover a completed uncertain build after checking source, actor and native completion. Optional recovery_job_id reconnects a proven owned application after its prior controller exits; never restarts or regenerates it.',{recovery_job_id:z.string().regex(/^[a-f0-9]{32}$/).optional()},a=>core.reconcile(a),false]")
p.write_text(s,encoding='utf-8')
