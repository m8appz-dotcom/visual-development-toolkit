import fs from 'node:fs/promises';
export async function inspectGlb(file){
 const b=await fs.readFile(file);if(b.length<20||b.toString('ascii',0,4)!=='glTF'||b.readUInt32LE(4)!==2||b.readUInt32LE(8)!==b.length)throw Error('INVALID_GLB');
 let json,bin;for(let at=12;at<b.length;){if(at+8>b.length)throw Error('CHUNK_BOUNDS');const n=b.readUInt32LE(at),type=b.readUInt32LE(at+4);if(n%4||at+8+n>b.length)throw Error('CHUNK_BOUNDS');if(type===0x4e4f534a){if(json)throw Error('DUPLICATE_JSON');json=JSON.parse(b.toString('utf8',at+8,at+8+n));}if(type===0x004e4942){if(bin)throw Error('DUPLICATE_BIN');bin=b.subarray(at+8,at+8+n);}at+=8+n;}
 if(!json||!bin||json.asset?.version!=='2.0'||json.buffers?.length!==1||json.buffers[0].uri||json.buffers[0].byteLength>bin.length)throw Error('GLB_BUFFER_SCHEMA');
 const index=(array,i,label)=>{if(!Number.isInteger(i)||i<0||i>=array.length)throw Error(label);return array[i];};
 const sizes={5121:1,5123:2,5125:4,5126:4},components={SCALAR:1,VEC3:3,VEC4:4,MAT4:16};
 function accessor(i,type,allowed){
  const a=index(json.accessors??[],i,'ACCESSOR_INDEX');if(a.sparse)throw Error('SPARSE_ACCESSOR_REQUIRES_SUPPORTED_VALIDATION');if(a.type!==type||!allowed.includes(a.componentType)||!Number.isInteger(a.count)||a.count<=0)throw Error('ACCESSOR_SCHEMA');
  const v=index(json.bufferViews??[],a.bufferView,'VIEW_INDEX'),count=components[a.type],size=sizes[a.componentType],stride=v.byteStride??count*size,offset=(v.byteOffset??0)+(a.byteOffset??0);
  if(v.buffer!==0||!Number.isInteger(stride)||stride<count*size||stride%size||!Number.isInteger(offset)||offset<0||offset%size||offset+(a.count-1)*stride+count*size>(v.byteOffset??0)+v.byteLength||(v.byteOffset??0)+v.byteLength>bin.length)throw Error('ACCESSOR_BOUNDS');
  const methods={5121:'readUInt8',5123:'readUInt16LE',5125:'readUInt32LE',5126:'readFloatLE'};
  return Array.from({length:a.count},(_,i)=>Array.from({length:count},(_,j)=>{let x=bin[methods[a.componentType]](offset+i*stride+j*size);if(a.normalized&&a.componentType!==5126)x/=a.componentType===5121?255:65535;return x;}));
 }
 const nodes=json.nodes??[],parents=new Map(),visited=new Set(),stack=new Set();
 function visit(i){index(nodes,i,'NODE_INDEX');if(stack.has(i))throw Error('NODE_CYCLE');if(visited.has(i))return;stack.add(i);const n=nodes[i];for(const k of ['matrix','translation','rotation','scale'])if(n[k]&&!n[k].every(Number.isFinite))throw Error('NODE_TRANSFORM_NONFINITE');if(n.scale?.some(x=>Math.abs(x)<1e-12))throw Error('NODE_SCALE_SINGULAR');for(const c of n.children??[]){if(parents.has(c)&&parents.get(c)!==i)throw Error('MULTIPLE_PARENTS');parents.set(c,i);visit(c);}stack.delete(i);visited.add(i);}
 for(let i=0;i<nodes.length;i++)visit(i);
 function nonsingular(m){const a=[...m];for(let c=0;c<4;c++){let p=c;for(let r=c+1;r<4;r++)if(Math.abs(a[c*4+r])>Math.abs(a[c*4+p]))p=r;if(Math.abs(a[c*4+p])<1e-12)return false;for(let k=0;k<4;k++)[a[k*4+c],a[k*4+p]]=[a[k*4+p],a[k*4+c]];for(let r=c+1;r<4;r++){const f=a[c*4+r]/a[c*4+c];for(let k=c+1;k<4;k++)a[k*4+r]-=f*a[k*4+c];}}return true;}
 const checks=[],primitives=[],staticMeshes=[];let joints=0;
 for(const skin of json.skins??[]){if(!Array.isArray(skin.joints)||!skin.joints.length||new Set(skin.joints).size!==skin.joints.length)throw Error('SKIN_JOINTS_INVALID');for(const j of skin.joints)index(nodes,j,'SKIN_JOINT_INDEX');joints+=skin.joints.length;if(skin.inverseBindMatrices!==undefined){const matrices=accessor(skin.inverseBindMatrices,'MAT4',[5126]);checks.push({name:'finite_invertible_bind_matrices',passed:matrices.length===skin.joints.length&&matrices.every(m=>m.every(Number.isFinite)&&nonsingular(m))});}}
 for(const [nodeIndex,node]of nodes.entries())if(node.mesh!==undefined){
  const mesh=index(json.meshes??[],node.mesh,'MESH_INDEX');if(node.skin===undefined){staticMeshes.push({node:nodeIndex,name:node.name??'',parent:parents.get(nodeIndex)??null});continue;}
  const skin=index(json.skins??[],node.skin,'SKIN_INDEX');for(const p of mesh.primitives??[]){
   const pos=accessor(p.attributes.POSITION,'VEC3',[5126]),weights=accessor(p.attributes.WEIGHTS_0,'VEC4',[5121,5123,5126]),ids=accessor(p.attributes.JOINTS_0,'VEC4',[5121,5123]);if(weights.length!==pos.length||ids.length!==pos.length)throw Error('ATTRIBUTE_COUNT_MISMATCH');
   let w1,j1;if(p.attributes.WEIGHTS_1!==undefined||p.attributes.JOINTS_1!==undefined){w1=accessor(p.attributes.WEIGHTS_1,'VEC4',[5121,5123,5126]);j1=accessor(p.attributes.JOINTS_1,'VEC4',[5121,5123]);if(w1.length!==pos.length||j1.length!==pos.length)throw Error('ATTRIBUTE_COUNT_MISMATCH');}
   let unweighted=0,badSums=0,badIds=0,badNumbers=0;for(let i=0;i<pos.length;i++){const w=[...weights[i],...(w1?.[i]??[])],js=[...ids[i],...(j1?.[i]??[])],sum=w.reduce((a,v)=>a+v,0);if(sum<=1e-8)unweighted++;if(Math.abs(sum-1)>.002)badSums++;if(!pos[i].every(Number.isFinite)||w.some(v=>!Number.isFinite(v)||v<0))badNumbers++;if(js.some(v=>!Number.isInteger(v)||v<0||v>=skin.joints.length))badIds++;}
   if(p.indices!==undefined&&accessor(p.indices,'SCALAR',[5121,5123,5125]).some(([v])=>!Number.isInteger(v)||v<0||v>=pos.length))throw Error('TRIANGLE_INDEX_INVALID');
   primitives.push({node:nodeIndex,vertices:pos.length,unweighted,bad_weight_sums:badSums,invalid_joint_indices:badIds,nonfinite_or_negative:badNumbers});
  }
 }
 checks.push({name:'skinned_primitives_present',passed:primitives.length>0},{name:'weights_and_positions',passed:primitives.length>0&&primitives.every(p=>!p.unweighted&&!p.bad_weight_sums&&!p.invalid_joint_indices&&!p.nonfinite_or_negative)});
 return {verdict:checks.some(c=>!c.passed)?'failed':staticMeshes.length?'needs_review':'passed',checks,primitives,static_meshes:staticMeshes,skins:json.skins?.length??0,joints,limitations:['Structure does not establish anatomical or visual acceptance. Static pieces require attachment review.']};
}
