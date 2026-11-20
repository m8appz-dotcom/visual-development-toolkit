import {Workflow as Previous} from './workflow-v03.mjs';
import {ROOT} from './accurig.mjs';
import fs from 'node:fs/promises';
import cp from 'node:child_process';
const PY='D:/visual-development-toolkit/windows/venv/Scripts/python.exe';
export class Workflow extends Previous{
 constructor(){super();this.baseGateReceipt=null;}
 async checkBaseGate(input){
  if(!this.baseGateReceipt)throw Error('BASE_REVIEW_REQUIRED: inspect base mesh before AccuRIG');
  const args=[ROOT+'/scripts/base_gate.py','assert','--receipt',this.baseGateReceipt,'--input',input];
  const value=await new Promise((resolve,reject)=>cp.execFile(PY,args,{windowsHide:true,timeout:30000},(e,out)=>{
   try{const r=JSON.parse(out);if(e||!r.ok)reject(Error('BASE_GATE_BLOCKED: '+(r.error??e?.message)));else resolve(r.result);}
   catch(parse){reject(Error('BASE_GATE_VERIFICATION_FAILED: '+(e?.message??parse.message)));}
  }));return value;
 }
 async setBaseGate(receipt){
  if(this.active||this.uncertain)throw Error('BUSY_OR_UNCERTAIN');
  const previous=this.baseGateReceipt;this.baseGateReceipt=receipt;
  try{const r=JSON.parse(await fs.readFile(receipt,'utf8'));const verified=await this.checkBaseGate(r.model.path);return {receipt,...verified};}
  catch(e){this.baseGateReceipt=previous;throw e;}
 }
 async load(input){this.guard();await this.checkBaseGate(input);return super.load(input);}
 async checkLoadedBase(){const r=await this.checkBaseGate(this.model?.path);if(r.source_sha256!==this.model?.sha256)throw Error('LOADED_BASE_SOURCE_CHANGED');return r;}
 async build(){this.guard();await this.checkLoadedBase();return super.build();}
 async detect(options){this.guard();await this.checkLoadedBase();return super.detect(options);}
 async rig(options){this.guard();await this.checkLoadedBase();return super.rig(options);}
 async status(){return {...await super.status(),base_gate_receipt:this.baseGateReceipt};}
}
