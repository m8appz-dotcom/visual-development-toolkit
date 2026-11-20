import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {Workflow} from '../src/workflow.mjs';
import {inspectJoints,assertJointReview} from '../src/joints-quality.mjs';
import {assertReadback,atomicJson,manifest,verifyManifest,publishExclusive,fileHash} from '../src/integrity.mjs';
import {inspectGlb} from '../src/quality.mjs';
import {BUILD_WAIT_MS,buildEvidence} from '../src/build-recovery.mjs';
import {claimLease,assertLease,releaseLease} from '../src/lease.mjs';
const tick=()=>new Promise(r=>setTimeout(r,40));
function fake(){const w=new Workflow();w.cdp={};w.checkLease=async()=>{};w.checkBaseGate=async()=>({source_sha256:w.model?.sha256});w.persist=async()=>{};return w;}
test('F1/F2 empty, missing and collapsed joints cannot be reviewed or built',async()=>{
 const q=inspectJoints({bodyJoints:[],fingerJoints:[]});assert.equal(q.finite_positions,false);assert.equal(q.verdict,'failed');assert.throws(()=>assertJointReview(null,q,{sha256:'x'},0),/ANATOMY_FAILED/);
 const w=fake();w.model={prepared:true};w.snapshot=async()=>({bodyJoints:[],fingerJoints:[]});await assert.rejects(()=>w.build(),/ANATOMY_FAILED/);
});
test('F1 Nico erroneous chain from actual detection is rejected',async()=>{
 const cp=JSON.parse(await fs.readFile(new URL('../data/checkpoints/82c54348dcec4860ac57b97b53293fb5.json',import.meta.url)));const q=inspectJoints(cp.joints);assert.ok(q.errors.some(e=>e.code==='COLLAPSED_FINGER_CHAIN'&&e.side==='R'&&e.finger==='Index'));
});
test('F1 accepted joint review is bound to exact revision and hash',()=>{
 const q={errors:[],joints_sha256:'a'};const model={sha256:'source'};const r={revision:2,model_sha256:'source',joints_sha256:'a',verdict:'accepted'};assert.doesNotThrow(()=>assertJointReview(r,q,model,2));assert.throws(()=>assertJointReview(r,q,model,3),/REVIEW_REQUIRED/);
});
test('F3 structural pass cannot enable export without exact visual review',async()=>{
 const dir=await fs.mkdtemp(path.join(os.tmpdir(),'accurig-review-'));try{const file=dir+'/x.glb';await fs.writeFile(file,'fixture');const h=await fileHash(file),w=fake();w.model={path:file,sha256:h};w.generation={id:'g',revision:0,preview:{path:file,sha256:h}};w.validation={generation_id:'g',structure:'passed',deformation:'passed',preview_sha256:h};await assert.rejects(()=>w.assertGeneration({visual:true}),/VISUAL_REVIEW_REQUIRED/);}finally{await fs.rm(dir,{recursive:true});}
});
test('F5 artifact hash change invalidates accepted generation',async()=>{
 const dir=await fs.mkdtemp(path.join(os.tmpdir(),'accurig-hash-'));try{const file=dir+'/x.glb';await fs.writeFile(file,'before');const h=await fileHash(file),w=fake();w.model={path:file,sha256:h};w.generation={id:'g',revision:0,preview:{path:file,sha256:h}};await fs.writeFile(file,'after');await assert.rejects(()=>w.assertGeneration(),/ARTIFACT_CHANGED/);}finally{await fs.rm(dir,{recursive:true});}
});
test('F6 reset clears model, acceptance, offline privileges and joint review',()=>{const w=fake();Object.assign(w,{model:{},generation:{},validation:{},visualReview:{},jointReview:{},offlineRecovery:true});w.resetSession();assert.equal(w.model,null);assert.equal(w.generation,null);assert.equal(w.validation,null);assert.equal(w.visualReview,null);assert.equal(w.jointReview,null);assert.equal(w.offlineRecovery,false);});
test('F9 failed old job cannot clear a newer reservation',async()=>{const w=fake();let finish;const j=await w.job('validate',()=>new Promise(r=>finish=r));await tick();w.active='new';finish({});await tick();assert.equal(w.active,'new');assert.equal((await w.jobStatus(j.id)).state,'completed');});
test('F10 failed initial persistence leaves no false busy state or native call',async()=>{const w=fake();let called=false;w.persist=async()=>{throw Error('disk full');};await assert.rejects(()=>w.job('build',async()=>{called=true;}),/disk full/);assert.equal(w.active,null);assert.equal(called,false);assert.equal(w.jobs.size,0);});
test('F10 atomic JSON preserves complete existing JSON when serialization fails',async()=>{const dir=await fs.mkdtemp(path.join(os.tmpdir(),'accurig-json-'));try{const file=dir+'/state.json';await atomicJson(file,{before:true});const circular={};circular.self=circular;await assert.rejects(()=>atomicJson(file,circular));assert.deepEqual(JSON.parse(await fs.readFile(file)),{before:true});assert.equal((await fs.readdir(dir)).length,1);}finally{await fs.rm(dir,{recursive:true});}});
test('F11 mask readback and quaternion equivalence are verified',()=>{assert.throws(()=>assertReadback({name:'j',masked:false},{masked:true}),/MASK_READBACK/);assert.doesNotThrow(()=>assertReadback({name:'j',rotation:{x:0,y:0,z:0,w:1}},{rotation:{x:0,y:0,z:0,w:-1}}));});
test('F11 unverified rollback is uncertain instead of completed',async()=>{const w=fake();w.model={prepared:true};w.snapshot=async()=>({bodyJoints:[{name:'j',masked:true,position:{x:0,y:0,z:0}}],fingerJoints:[]});w.checkpoint=async()=>({id:'x'});w.apply=async()=>{};const j=await w.edit({expected_revision:0,coordinate_space:'accurig_native_model',changes:[{name:'j',masked:false}]});await tick();assert.equal((await w.jobStatus(j.id)).state,'failed');assert.match(w.jobs.get(j.id).error,/MASK_READBACK/);});
test('F12 changed process identity blocks closure before a quit request',async()=>{const w=fake();w.identity={pid:process.pid,owned:true,process_created:'wrong',executable:process.execPath};let called=false;w.main=async()=>{called=true;};await assert.rejects(()=>w.close(),/OWNED_PROCESS_MISMATCH/);assert.equal(called,false);assert.ok(w.cdp);});
test('F13 bounded 90 minute wait still requires actual complete events',()=>{assert.equal(BUILD_WAIT_MS,5400000);assert.equal(buildEvidence([{at:2,channel:'onProgressChange',data:{processTitle:16,status:1}}],1).complete,false);});
test('F14 entire backup manifest is verified, including avatar and metadata',async()=>{const dir=await fs.mkdtemp(path.join(os.tmpdir(),'accurig-backup-'));try{await fs.writeFile(dir+'/a.glb','glb');await fs.writeFile(dir+'/a.iAvatar','avatar');const m=await manifest(dir);await verifyManifest(dir,m);await fs.writeFile(dir+'/a.iAvatar','corrupted');await assert.rejects(()=>verifyManifest(dir,m),/MANIFEST_MISMATCH/);}finally{await fs.rm(dir,{recursive:true});}});
test('F15 exclusive publication cannot leave partial final outputs',async()=>{const dir=await fs.mkdtemp(path.join(os.tmpdir(),'accurig-publish-'));try{await fs.writeFile(dir+'/source','x');await fs.writeFile(dir+'/collision','keep');await assert.rejects(()=>publishExclusive([[dir+'/source',dir+'/new'],[dir+'/source',dir+'/collision']],dir+'/receipt'));await assert.rejects(()=>fs.access(dir+'/new'));assert.equal(await fs.readFile(dir+'/collision','utf8'),'keep');}finally{await fs.rm(dir,{recursive:true});}});
test('deletion requires explicit exact generation confirmation',async()=>{const w=fake();w.lease=null;await assert.rejects(()=>w.deleteGeneration({generation_id:'a',confirm_generation_id:'b'}));});
