import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import crypto from 'node:crypto';
import {completeBuild,readBuildEvidence} from '../src/build-recovery.mjs';
import {fileHash} from '../src/integrity.mjs';
import {ROOT} from '../src/accurig.mjs';
function glb(){const bin=Buffer.alloc(36);bin.writeFloatLE(1,12);const j={asset:{version:'2.0'},buffers:[{byteLength:36}],bufferViews:[{buffer:0,byteOffset:0,byteLength:12},{buffer:0,byteOffset:12,byteLength:16},{buffer:0,byteOffset:28,byteLength:8}],accessors:[{bufferView:0,componentType:5126,count:1,type:'VEC3'},{bufferView:1,componentType:5126,count:1,type:'VEC4'},{bufferView:2,componentType:5123,count:1,type:'VEC4'}],nodes:[{mesh:0,skin:0},{}],skins:[{joints:[1]}],meshes:[{primitives:[{attributes:{POSITION:0,WEIGHTS_0:1,JOINTS_0:2}}]}]};let txt=Buffer.from(JSON.stringify(j));txt=Buffer.concat([txt,Buffer.alloc((4-txt.length%4)%4,32)]);const b=Buffer.alloc(28+txt.length+bin.length);b.write('glTF');b.writeUInt32LE(2,4);b.writeUInt32LE(b.length,8);b.writeUInt32LE(txt.length,12);b.writeUInt32LE(0x4e4f534a,16);txt.copy(b,20);b.writeUInt32LE(bin.length,20+txt.length);b.writeUInt32LE(0x004e4942,24+txt.length);bin.copy(b,28+txt.length);return b;}
test('F7 fresh complete build automatically records verifiable recovery receipt without clearing reservation',async()=>{
 const dir=await fs.mkdtemp(path.join(os.tmpdir(),'accurig-completion-')),id=crypto.randomBytes(16).toString('hex');
 try{
  const source=dir+'/source.fbx',avatar=dir+'/accurig.iAvatar',preview=dir+'/accurig.glb';await fs.writeFile(source,'original');await fs.writeFile(avatar,'avatar');await fs.writeFile(preview,glb());const sha=await fileHash(source),started=Date.now()-1000;
  const events=[{at:started+1,channel:'oniAvatarExported',data:{iAvatarPath:avatar}},{at:started+2,channel:'onProgressChange',data:{processTitle:16,status:1}},{at:started+3,channel:'onGlbConvetedInAccuRig'}];
  const model={path:source,sha256:sha},job={id,started,revision:1,build_context:{model,actor_id:'owned',joints_before:{}}};const core={model,revision:1,active:id,persist:async()=>{},main:async()=>({pid:42,cpu:{user:1},events}),renderer:async()=>({cid:'owned',glb:preview,iAvatar:avatar}),snapshot:async()=>({})};
  const r=await completeBuild(core,job);assert.equal(core.active,id);assert.equal(r.generation_id,id);const receipt=JSON.parse(await fs.readFile(job.build_context.completion_receipt.path));assert.equal(receipt.model_sha256,sha);assert.equal(receipt.actor_id,'owned');assert.equal(await fileHash(job.build_context.completion_receipt.path),job.build_context.completion_receipt.sha256);assert.equal(receipt.glb_sha256,await fileHash(preview));assert.equal(core.validation,null);
 }finally{await fs.rm(dir,{recursive:true});for(const f of [ROOT+'/data/rig-'+id+'.glb',ROOT+'/data/completion-'+id+'.json'])await fs.unlink(f).catch(()=>{});}
});
test('F7 completion cannot silently adopt another actor',async()=>{
 const dir=await fs.mkdtemp(path.join(os.tmpdir(),'accurig-actor-'));try{const src=dir+'/source';await fs.writeFile(src,'x');const model={path:src,sha256:await fileHash(src)},started=Date.now()-1000;const core={model,revision:1,persist:async()=>{},main:async()=>({events:[{at:started+1,channel:'onProgressChange',data:{processTitle:16,status:1}},{at:started+2,channel:'onGlbConvetedInAccuRig'}]}),renderer:async()=>({cid:'wrong',glb:'unused',iAvatar:'unused'})};await assert.rejects(()=>completeBuild(core,{id:'test',revision:1,started,build_context:{model,actor_id:'expected'}}),/ACTOR_CHANGED/);}finally{await fs.rm(dir,{recursive:true});}
});
test('F13 no CPU or native activity is observable without cancelling/replaying a native job',async()=>{
 const now=Date.now,job={started:0,progress:{native:null,cpu:{user:1},last_activity_at:0}},core={main:async()=>({pid:42,events:[],cpu:{user:1}}),persist:async()=>{}};
 try{Date.now=()=>600001;const result=await readBuildEvidence(core,job);assert.equal(result.complete,false);assert.equal(job.progress.health,'no_recent_activity');assert.equal(job.state,undefined);}finally{Date.now=now;}
});
