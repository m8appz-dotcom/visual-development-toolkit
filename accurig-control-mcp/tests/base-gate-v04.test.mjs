import test from 'node:test';
import assert from 'node:assert/strict';
import {Workflow} from '../src/workflow.mjs';
test('missing base review blocks native import before IPC and preserves current model',async()=>{
 const w=new Workflow();w.cdp={};w.model={path:'keep.fbx'};w.main=()=>{throw Error('must not call IPC');};
 await assert.rejects(()=>w.load('unreviewed.fbx'),/BASE_REVIEW_REQUIRED/);assert.equal(w.model.path,'keep.fbx');
});
test('missing base review blocks skin before joint snapshot or generation',async()=>{
 const w=new Workflow();w.cdp={};w.model={path:'keep.fbx'};w.snapshot=()=>{throw Error('must not inspect joints');};
 await assert.rejects(()=>w.build(),/BASE_REVIEW_REQUIRED/);assert.equal(w.active,null);
});
test('invalid receipt cannot replace a previous bound base review',async()=>{
 const w=new Workflow();w.baseGateReceipt='previous';await assert.rejects(()=>w.setBaseGate('missing-receipt.json'));assert.equal(w.baseGateReceipt,'previous');
});
test('compatibility generate and detection cannot run on an unreviewed base',async()=>{
 const w=new Workflow();w.cdp={};w.model={path:'keep.fbx'};
 await assert.rejects(()=>w.rig({}),/BASE_REVIEW_REQUIRED/);
 await assert.rejects(()=>w.detect({}),/BASE_REVIEW_REQUIRED/);
});
test('a newer review of a replaced file cannot approve the older model loaded in memory',async()=>{
 const w=new Workflow();w.cdp={};w.model={path:'source.fbx',sha256:'old'};w.checkBaseGate=async()=>({source_sha256:'new'});
 await assert.rejects(()=>w.build(),/LOADED_BASE_SOURCE_CHANGED/);
});
