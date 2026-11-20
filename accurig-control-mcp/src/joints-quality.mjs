import {digest} from './integrity.mjs';
export const jointHash=j=>digest(JSON.stringify(j));
const distance=(a,b)=>Math.hypot(...['x','y','z'].map(k=>a[k]-b[k]));
const bodyNames=['Hip','NeckTwist01','Head',...['L','R'].flatMap(s=>['Thigh','Calf','Foot','ToeBase','Clavicle','Upperarm','Forearm','Hand'].map(n=>s+'_'+n))].map(n=>'CC_Base_'+n);
export function inspectJoints(data,{fingers='Both',finger_count=5}={}){
 const body=data?.bodyJoints??[],hands=data?.fingerJoints??[],all=[...body,...hands],byName=new Map(all.map(j=>[j.name,j]));
 const errors=[],warnings=[],chains=[];
 if(!body.length)errors.push({code:'EMPTY_BODY'});
 for(const name of bodyNames)if(!byName.has(name))errors.push({code:'MISSING_BODY_JOINT',name});
 if(byName.size!==all.length)errors.push({code:'DUPLICATE_JOINT_NAMES'});
 for(const j of all)if(!j.position||!['x','y','z'].every(k=>Number.isFinite(j.position[k])))errors.push({code:'INVALID_POSITION',name:j.name});
 const finite=all.length>0&&all.every(j=>j.position&&['x','y','z'].every(k=>Number.isFinite(j.position[k])));
 const bounds=finite?Object.fromEntries(['x','y','z'].map(k=>[k,{min:Math.min(...all.map(j=>j.position[k])),max:Math.max(...all.map(j=>j.position[k]))}])):null;
 const height=bounds?bounds.y.max-bounds.y.min:0;
 if(finite&&height<=0)errors.push({code:'DEGENERATE_BODY_EXTENT'});
 for(const side of ['L','R']){
  const required=finger_count>0&&(fingers==='Both'||fingers===(side==='L'?'Left':'Right'));
  let present=0;
  for(const finger of ['Thumb','Index','Mid','Ring','Pinky']){
   const names=['1','2','3','Tip'].map(n=>'CC_Base_'+side+'_'+finger+n),js=names.map(n=>byName.get(n));
   if(js.every(j=>j?.masked))continue;
   if(!js.some(Boolean)){if(required&&finger_count===5)errors.push({code:'MISSING_FINGER',side,finger});continue;}
   if(!js.every(Boolean)){errors.push({code:'INCOMPLETE_FINGER_CHAIN',side,finger});continue;}
   if(!js.every(j=>j.position&&Object.values(j.position).every(Number.isFinite)))continue;
   present++;const lengths=js.slice(1).map((j,i)=>distance(j.position,js[i].position));
   const smallest=Math.min(...lengths),ratio=Math.max(...lengths)/Math.max(smallest,1e-12);
   chains.push({side,finger,lengths,ratio});
   if(smallest<height*.0005||ratio>8)errors.push({code:'COLLAPSED_FINGER_CHAIN',side,finger,lengths,ratio});
   else if(ratio>4)warnings.push({code:'FINGER_LENGTH_RATIO_REVIEW',side,finger,lengths,ratio});
   for(let i=0;i<2;i++){
    const a=['x','y','z'].map(k=>js[i+1].position[k]-js[i].position[k]),b=['x','y','z'].map(k=>js[i+2].position[k]-js[i+1].position[k]);
    const cosine=a.reduce((s,v,k)=>s+v*b[k],0)/Math.max(lengths[i]*lengths[i+1],1e-12);
    if(cosine<-.25)warnings.push({code:'FINGER_REVERSAL_REVIEW',side,finger,joint:i+2,cosine});
   }
   const wrist=byName.get('CC_Base_'+side+'_Hand');
   if(wrist&&distance(wrist.position,js[0].position)>height*.12)errors.push({code:'FINGER_BASE_TOO_FAR_FROM_WRIST',side,finger});
  }
  if(required&&present<finger_count)errors.push({code:'MISSING_CONFIGURED_FINGERS',side,expected:finger_count,actual:present});
  for(const [a,b]of [['Upperarm','Forearm'],['Forearm','Hand'],['Thigh','Calf'],['Calf','Foot']]){
   const x=byName.get('CC_Base_'+side+'_'+a),y=byName.get('CC_Base_'+side+'_'+b);
   if(x&&y&&finite&&distance(x.position,y.position)<height*.01)errors.push({code:'COLLAPSED_LIMB',side,a,b});
  }
 }
 return {verdict:errors.length?'failed':warnings.length?'needs_review':'passed',joint_count:all.length,finite_positions:finite,bounds,chains,errors,warnings,joints_sha256:jointHash(data),limitations:['Spatial fit and anatomical identity require the explicit multi-view review. Asymmetry is not an instruction to mirror anatomy.']};
}
export function assertJointReview(review,quality,model,revision){
 if(quality.errors.length)throw Error('JOINT_ANATOMY_FAILED: '+JSON.stringify(quality.errors));
 if(!review||review.revision!==revision||review.model_sha256!==model.sha256||review.joints_sha256!==quality.joints_sha256||review.verdict!=='accepted')throw Error('JOINT_REVIEW_REQUIRED');
}
