import test from 'node:test';
import assert from 'node:assert/strict';
import {Workflow} from '../src/workflow.mjs';
const tick=()=>new Promise(r=>setTimeout(r,30));
// These lifecycle fixtures isolate the pre-existing contracts after a base review.
class MockWorkflow extends Workflow{async checkLease(){} async checkBaseGate(){return {source_sha256:this.model?.sha256};}} 
test('native timeout remains uncertain and blocks new operations',async()=>{const w=new MockWorkflow();w.cdp={};w.persist=async()=>{};const j=await w.job('build',async()=>{throw Error('Inspector request timed out: Runtime.evaluate');});await tick();assert.equal((await w.jobStatus(j.id)).state,'uncertain');assert.equal(w.active,j.id);assert.throws(()=>w.guard(),/UNCERTAIN/);w.main=async()=>false;assert.equal((await w.reconcile()).state,'uncertain');assert.throws(()=>w.guard(),/UNCERTAIN/);});
test('preflight failure cannot start a native generation',async()=>{const w=new MockWorkflow();w.cdp={};w.model={prepared:true};w.generation={id:'old',revision:0};w.rigged=true;w.snapshot=async()=>{throw Error('native failure');};await assert.rejects(()=>w.build(),/native failure/);assert.equal(w.active,null);assert.equal(w.generation.id,'old');});
test('failed import invalidates prior model and export state',async()=>{const w=new MockWorkflow();w.cdp={};w.model={prepared:true};w.rigged=true;w.generation={id:'old',revision:0};await assert.rejects(()=>w.load('D:/visual-development-toolkit/accurig-control-mcp/does-not-exist.obj'));assert.equal(w.model,null);assert.equal(w.generation,null);assert.equal(w.rigged,false);});
test('close clears model and rig state even without an application',async()=>{const w=new MockWorkflow();w.model={prepared:true};w.rigged=true;w.generation={id:'old'};await w.close();assert.equal(w.model,null);assert.equal(w.generation,null);assert.equal(w.rigged,false);});
test('revision conflict cannot invoke native edits',async()=>{const w=new MockWorkflow();w.cdp={};w.revision=3;w.snapshot=()=>{throw Error('must not run');};await assert.rejects(()=>w.edit({expected_revision:2,changes:[],coordinate_space:'accurig_native_model'}),/REVISION_CONFLICT/);});

test('independent validator timeout does not pretend the native SDK is busy',async()=>{const w=new MockWorkflow();w.cdp={};w.persist=async()=>{};const j=await w.job('validate',async()=>{throw Error('Independent Blender validation timed out');});await tick();assert.equal((await w.jobStatus(j.id)).state,'failed');assert.equal(w.active,null);assert.equal(w.uncertain,null);});

test('a persisted running job is not reported as attached after server restart',async()=>{const fs=await import('node:fs/promises');const crypto=await import('node:crypto');const {ROOT}=await import('../src/accurig.mjs');const id=crypto.randomBytes(16).toString('hex');const file=ROOT+'/data/jobs/'+id+'.json';await fs.mkdir(ROOT+'/data/jobs',{recursive:true});await fs.writeFile(file,JSON.stringify({id,state:'working',type:'build'}),{flag:'wx'});try{const w=new MockWorkflow();const result=await w.jobStatus(id);assert.equal(result.state,'interrupted');assert.equal(result.recorded_state,'working');}finally{await fs.unlink(file);}});

test('invalid calibration cannot change the accepted generation',async()=>{const w=new MockWorkflow();w.cdp={};w.generation={id:'accepted',revision:0};w.snapshot=async()=>({bodyJoints:[{name:'CC_Base_Hip'}],fingerJoints:[]});w.assertGeneration=async()=>w.generation;await assert.rejects(()=>w.calibrate({coordinate_space:'accurig_native_angles',offsets:[{bone_name:'unknown',rotation:{x:0,y:0,z:0}}]}),/INVALID_CALIBRATION/);assert.equal(w.generation.id,'accepted');});

test('archive rejects an active owned history before reading or removing files',async()=>{const w=new MockWorkflow();w.cdp={};const id='a'.repeat(32);w.jobs.set(id,{id,state:'completed',type:'build',result:{preview:{actor_id:'own'}}});w.generation={actor_id:'own'};await assert.rejects(()=>w.archiveGeneration(id),/ACTIVE_HISTORY/);});

test('incomplete unreviewed generation cannot export',async()=>{const w=new MockWorkflow();w.cdp={};w.generation={id:'accepted',revision:0};w.validation={generation_id:'accepted',verdict:'needs_review'};await assert.rejects(()=>w.export('ignored.fbx'),/NO_CURRENT_GENERATION/);});

