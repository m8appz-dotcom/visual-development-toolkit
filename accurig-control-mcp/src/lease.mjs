import fs from 'node:fs/promises';
import {atomicJson} from './integrity.mjs';
import {processInfo} from './build-recovery.mjs';
import crypto from 'node:crypto';
export async function claimLease(root,identity){
 const file=root+'/data/controller-'+identity.pid+'.lease',token=crypto.randomUUID();
 const owner=await processInfo(process.pid),value={pid:process.pid,created:owner.created,app_pid:identity.pid,token};
 for(let retry=0;retry<3;retry++){
  try{const f=await fs.open(file,'wx');try{await f.writeFile(JSON.stringify(value));await f.sync();}finally{await f.close();}return {file,...value};}
  catch(e){if(e.code!=='EEXIST')throw e;const old=JSON.parse(await fs.readFile(file,'utf8')),p=await processInfo(old.pid);if(p?.created===old.created)throw Error('CONTROLLER_LEASE_IN_USE');await fs.rename(file,file+'.expired-'+crypto.randomUUID());}
 }throw Error('CONTROLLER_LEASE_BUSY');
}
export async function assertLease(lease){if(!lease)throw Error('CONTROLLER_LEASE_REQUIRED');const got=JSON.parse(await fs.readFile(lease.file,'utf8'));if(got.token!==lease.token||got.pid!==process.pid)throw Error('CONTROLLER_LEASE_LOST');}
export async function releaseLease(lease){if(!lease)return;await assertLease(lease);await fs.unlink(lease.file);}
