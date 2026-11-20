import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {inspectGlb} from '../src/quality.mjs';
import {claimLease,releaseLease} from '../src/lease.mjs';
function fixture(edit=()=>{}){
 const bin=Buffer.alloc(36);bin.writeFloatLE(1,12); // position0, weights[1,0,0,0], four ushort joint IDs.
 const j={asset:{version:'2.0'},buffers:[{byteLength:36}],bufferViews:[{buffer:0,byteOffset:0,byteLength:12},{buffer:0,byteOffset:12,byteLength:16},{buffer:0,byteOffset:28,byteLength:8}],accessors:[{bufferView:0,componentType:5126,count:1,type:'VEC3'},{bufferView:1,componentType:5126,count:1,type:'VEC4'},{bufferView:2,componentType:5123,count:1,type:'VEC4'}],nodes:[{mesh:0,skin:0},{name:'joint'}],skins:[{joints:[1]}],meshes:[{primitives:[{attributes:{POSITION:0,WEIGHTS_0:1,JOINTS_0:2}}]}]};edit(j,bin);let txt=Buffer.from(JSON.stringify(j));txt=Buffer.concat([txt,Buffer.alloc((4-txt.length%4)%4,32)]);const b=Buffer.alloc(28+txt.length+bin.length);b.write('glTF');b.writeUInt32LE(2,4);b.writeUInt32LE(b.length,8);b.writeUInt32LE(txt.length,12);b.writeUInt32LE(0x4e4f534a,16);txt.copy(b,20);b.writeUInt32LE(bin.length,20+txt.length);b.writeUInt32LE(0x004e4942,24+txt.length);bin.copy(b,28+txt.length);return b;
}
async function inspect(buffer){const dir=await fs.mkdtemp(path.join(os.tmpdir(),'accurig-glb-'));try{const p=dir+'/fixture.glb';await fs.writeFile(p,buffer);return await inspectGlb(p);}finally{await fs.rm(dir,{recursive:true});}}
test('strict synthetic structural fixture passes',async()=>assert.equal((await inspect(fixture())).verdict,'passed'));
test('floating/NaN JOINTS accessor is rejected',async()=>assert.rejects(()=>inspect(fixture(j=>{j.accessors[2].componentType=5126;})),/ACCESSOR_SCHEMA/));
test('out of bounds accessor is rejected',async()=>assert.rejects(()=>inspect(fixture(j=>{j.accessors[0].count=100;})),/ACCESSOR_BOUNDS/));
test('cyclic node hierarchy is rejected',async()=>assert.rejects(()=>inspect(fixture(j=>{j.nodes[0].children=[1];j.nodes[1].children=[0];})),/NODE_CYCLE/));
test('duplicate joint IDs are rejected',async()=>assert.rejects(()=>inspect(fixture(j=>{j.skins[0].joints=[1,1];})),/SKIN_JOINTS_INVALID/));
test('unskinned extra piece requires attachment review',async()=>{const q=await inspect(fixture(j=>{j.nodes.push({name:'loose-shirt',mesh:0});}));assert.equal(q.verdict,'needs_review');assert.equal(q.static_meshes[0].name,'loose-shirt');});
test('lease prevents simultaneous controllers',async()=>{const dir=await fs.mkdtemp(path.join(os.tmpdir(),'accurig-lease-'));try{await fs.mkdir(dir+'/data');const lease=await claimLease(dir,{pid:1234});await assert.rejects(()=>claimLease(dir,{pid:1234}),/LEASE_IN_USE/);await releaseLease(lease);}finally{await fs.rm(dir,{recursive:true});}});
