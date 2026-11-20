import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
export const digest=b=>crypto.createHash('sha256').update(b).digest('hex');
export const fileHash=async p=>digest(await fs.readFile(p));
export async function atomicJson(file,value){
 await fs.mkdir(path.dirname(file),{recursive:true});
 const tmp=file+'.'+crypto.randomUUID()+'.tmp';
 try{const f=await fs.open(tmp,'wx');try{await f.writeFile(JSON.stringify(value,null,2));await f.sync();}finally{await f.close();}await fs.rename(tmp,file);}
 finally{await fs.unlink(tmp).catch(e=>{if(e.code!=='ENOENT')throw e;});}
}
export async function manifest(dir){
 const base=await fs.realpath(dir),items=[];
 async function walk(relative){for(const entry of await fs.readdir(path.join(base,relative),{withFileTypes:true})){
  const rel=path.join(relative,entry.name),p=path.join(base,rel);
  if(entry.isSymbolicLink())throw Error('BACKUP_SYMLINK_REJECTED');
  if(entry.isDirectory())await walk(rel);else if(entry.isFile())items.push({relative:rel,bytes:(await fs.stat(p)).size,sha256:await fileHash(p)});
 }}
 await walk('');return items.sort((a,b)=>a.relative.localeCompare(b.relative));
}
export async function verifyManifest(dir,items){
 const got=await manifest(dir);if(digest(JSON.stringify(got))!==digest(JSON.stringify(items)))throw Error('BACKUP_MANIFEST_MISMATCH');return true;
}
export async function publishExclusive(files,receipt){
 const published=[];
 try{for(const [src,dst]of files){await fs.copyFile(src,dst,1);published.push(dst);}await atomicJson(receipt,{published,hashes:await Promise.all(published.map(async p=>({path:p,sha256:await fileHash(p)})))});}
 catch(e){for(const p of published)await fs.unlink(p).catch(()=>{});throw e;}
}
export function assertReadback(expected,actual,tolerance=.001){
 if(!actual)throw Error('JOINT_MISSING_ON_READBACK: '+expected.name);
 if(expected.masked!==undefined&&expected.masked!==actual.masked)throw Error('MASK_READBACK_FAILED: '+expected.name);
 for(const key of ['position','rotation'])if(expected[key]){
  const a=expected[key],b=actual[key];
  if(!b||Object.keys(a).some(k=>!Number.isFinite(b[k])))throw Error('EDIT_READBACK_FAILED: '+expected.name);
  // q and -q represent the same orientation.
  const error=Math.max(...Object.keys(a).map(k=>Math.abs(a[k]-b[k])));
  const opposite=key==='rotation'?Math.max(...Object.keys(a).map(k=>Math.abs(a[k]+b[k]))):Infinity;
  if(Math.min(error,opposite)>tolerance)throw Error('EDIT_READBACK_FAILED: '+expected.name);
 }
}
