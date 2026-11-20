import test from 'node:test';
import assert from 'node:assert/strict';
import {buildEvidence,waitForBuild,completeBuild,BUILD_WAIT_MS} from '../src/build-recovery.mjs';
import {Workflow} from '../src/workflow.mjs';
const finish={at:1600,channel:'onProgressChange',data:{processTitle:16,status:1}};
const glb={at:1700,channel:'onGlbConvetedInAccuRig'};
test('old completions, partial completion, native error cannot certify this build',()=>{
 assert.equal(buildEvidence([finish,glb],1800).complete,false);
 assert.equal(buildEvidence([finish],1000).complete,false);
 assert.equal(buildEvidence([{...glb,at:1500},finish],1000).complete,false);
 assert.equal(buildEvidence([finish,glb,{at:1800,channel:'onError',data:'failed'}],1000).complete,false);
 assert.equal(buildEvidence([finish,glb],1000).complete,true);
});
test('a 26 minute build is observed without replay or six-minute rejection',async()=>{
 let clock=0,calls=0;const job={started:0};
 const core={main:async()=>({pid:42,cpu:{user:clock*1000},events:clock>=26*60000?[{...finish,at:clock-1},{...glb,at:clock}]:[{at:clock,channel:'onProgressChange',data:{value:.2}}]}),persist:async()=>{calls++;}};
 const result=await waitForBuild(core,job,{now:()=>clock,sleep:async ms=>{clock+=ms;},pollMs:60000});
 assert.equal(result.complete,true);assert.equal(clock,26*60000);assert.ok(calls>6);assert.equal(job.progress.pid,42);assert.ok(BUILD_WAIT_MS>clock);
});
test('bounded wait still preserves uncertainty when there is no completion',async()=>{
 let clock=0;const job={started:0};const core={main:async()=>({events:[],pid:42,cpu:{user:clock}}),persist:async()=>{}};
 await assert.rejects(()=>waitForBuild(core,job,{timeoutMs:10,pollMs:5,now:()=>clock,sleep:async ms=>{clock+=ms;}}),/NATIVE_COMPLETION_UNCERTAIN/);
 assert.equal(clock,10);
});
test('a changed source/revision cannot be adopted as a completed rig',async()=>{
 const core={revision:4,model:{sha256:'current'}};
 await assert.rejects(()=>completeBuild(core,{revision:3,build_context:{model:{sha256:'old'}}}),/BUILD_CONTEXT_MISMATCH/);
});
test('reconciliation never releases a legacy build with no recovery identity',async()=>{
 const w=new Workflow();w.cdp={};w.active='old';w.uncertain={job_id:'old',type:'build',started:1};w.jobs.set('old',{id:'old'});
 const r=await w.reconcile();assert.equal(r.state,'uncertain');assert.equal(w.active,'old');assert.equal(w.rigged,false);assert.throws(()=>w.guard(),/UNCERTAIN/);
});
test('offline recovery permits validation only, never native edits or export',async()=>{
 const w=new Workflow();w.offlineRecovery=true;w.rigged=true;w.generation={id:'owned',revision:0};
 assert.throws(()=>w.guard(),/NOT_CONNECTED/);
 assert.doesNotThrow(()=>w.guard(true));
 await assert.rejects(()=>w.export('ignored.fbx'),/NOT_CONNECTED/);
 await assert.rejects(()=>w.build(),/NOT_CONNECTED/);
});
