"""All-mesh structural/deformation screens. Visual acceptance is always separate."""
import bpy,sys,json,pathlib,math,hashlib,numpy as np
from mathutils import Vector,Quaternion
source,output=sys.argv[sys.argv.index('--')+1:];source=pathlib.Path(source);output=pathlib.Path(output)
before=set(bpy.data.objects)
if source.suffix.lower()=='.fbx':bpy.ops.import_scene.fbx(filepath=str(source))
else:bpy.ops.import_scene.gltf(filepath=str(source))
objects=[o for o in bpy.data.objects if o not in before];arms=[o for o in objects if o.type=='ARMATURE'];helpers={b.custom_shape for a in arms for b in a.pose.bones if b.custom_shape};meshes=[o for o in objects if o.type=='MESH' and o not in helpers]
report={'source':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'checks':[],'meshes':[],'poses':[],'pose_plan':[],'visual':'pending','ready_for_delivery':False,'limitations':['Geometric screens do not certify anatomical appearance. Exact reviewed GLB and all motions must be observed.','Collision screen tests non-coplanar triangle crossings in affected regions, capped at2000 candidate pairs; contacts, coplanar overlaps and complete cloth physics are not certified.']}
def check(check_name,passed,/,**details):report['checks'].append({'name':check_name,'passed':bool(passed),'details':details})
check('armature_and_mesh',len(arms)==1 and bool(meshes))
if len(arms)!=1 or not meshes:raise RuntimeError('Expected one armature and meshes')
arm=arms[0];bones=arm.pose.bones
def find(s):return next((b for b in bones if b.name==s or b.name.endswith('_'+s)),None)
def point(s):
 b=find(s)
 if b is None:raise ValueError('Required bone absent: '+s)
 return arm.matrix_world@b.head
def unit(v,fallback=(1,0,0)):return v.normalized() if v.length>1e-8 else Vector(fallback)
saved={b.name:(b.rotation_mode,b.matrix_basis.copy()) for b in bones}
arm.animation_data_clear()
def reset():
 for b in bones:b.rotation_mode=saved[b.name][0];b.matrix_basis=saved[b.name][1]
 bpy.context.view_layer.update()
def coords(o):
 evaluated=o.evaluated_get(bpy.context.evaluated_depsgraph_get());a=np.empty(len(evaluated.data.vertices)*3,dtype=np.float64);evaluated.data.vertices.foreach_get('co',a);a=a.reshape((-1,3));m=np.array(o.matrix_world);return a@m[:3,:3].T+m[:3,3]
reset();rests={o.name:coords(o) for o in meshes};allcoords=np.concatenate(list(rests.values()));height=max(float(np.ptp(allcoords[:,2])),1e-8)
names={b.name for b in arm.data.bones};weighted_names=set();edge_arrays={};triangles={}
check('bind_transforms',all(math.isfinite(v) for b in arm.data.bones for row in b.matrix_local for v in row) and all(abs(b.matrix_local.determinant())>1e-12 for b in arm.data.bones))
for o in meshes:
 ids={g.index for g in o.vertex_groups if g.name in names};unweighted=bad=nonfinite=0
 for v in o.data.vertices:
  ws=[g.weight for g in v.groups if g.group in ids];total=sum(ws);unweighted+=total<=1e-8;bad+=abs(total-1)>.002;nonfinite+=any(not math.isfinite(w) or w<0 for w in ws)
  for g in v.groups:
   if g.group in ids and g.weight>1e-8:weighted_names.add(o.vertex_groups[g.group].name.removeprefix('CC_Base_'))
 mods=sum(m.type=='ARMATURE' and m.object==arm for m in o.modifiers);attached=o.parent_type=='BONE' and o.parent==arm
 info={'name':o.name,'vertices':len(o.data.vertices),'triangles':sum(len(p.vertices)-2 for p in o.data.polygons),'unweighted':unweighted,'bad_weight_sums':bad,'nonfinite_or_negative':nonfinite,'armature_modifiers':mods,'rigid_bone_attachment':attached};report['meshes'].append(info)
 check('weights:'+o.name,not(nonfinite or bad or (unweighted and not attached)) and bool(mods or attached),**info)
 edges=np.array([tuple(e.vertices) for e in o.data.edges],dtype=np.int32);edge_arrays[o.name]=edges
 o.data.calc_loop_triangles();triangles[o.name]=np.array([tuple(t.vertices) for t in o.data.loop_triangles],dtype=np.int32)
report['deform_bones']=sorted(weighted_names)
up=unit(point('Head')-point('Hip'),(0,0,1));lateral=unit(point('L_Upperarm')-point('R_Upperarm'));front=unit(lateral.cross(up),(0,-1,0))
def move(s,axis,angle):return {'bone':find(s).name if find(s) else s,'world_axis_blender':list(unit(axis)),'angle':angle}
plans=[]
def add(name,moves,region):plans.append({'name':name,'moves':moves,'region':region})
for side,sign in [('L',1),('R',-1)]:
 add(side+'_shoulder',[move(side+'_Clavicle',front,sign*.2),move(side+'_Upperarm',front,sign*.6)],'shoulder')
 direction=unit(point(side+'_Hand')-point(side+'_Forearm'))
 add(side+'_elbow',[move(side+'_Forearm',direction.cross(front),1.15)],'elbow')
 add(side+'_forearm_twist',[move(side+'_Forearm',direction,sign*.7)],'wrist')
 add(side+'_hip',[move(side+'_Thigh',lateral,-.7)],'hip')
 add(side+'_knee',[move(side+'_Calf',lateral,1.15)],'knee')
 handlong=unit(point(side+'_Mid1')-point(side+'_Hand'))
 across=unit(point(side+'_Pinky1')-point(side+'_Index1'))
 # Radial->ulnar order reverses handedness. Without side correction the right
 # test hyperextends while the left flexes, even on an otherwise valid CC rig.
 palmnormal=unit(handlong.cross(across))*sign;flex=unit(handlong.cross(-palmnormal))
 add(side+'_wrist',[move(side+'_Hand',flex,.55)],'wrist')
 fist=[]
 for finger in ['Index','Mid','Ring','Pinky']:
  for number,angle in [(1,.8),(2,1.1),(3,.75)]:fist.append(move(side+'_'+finger+str(number),flex,angle))
 add(side+'_fist',fist,'hand')
 thumbdir=unit(point(side+'_Thumb3')-point(side+'_Thumb1'));target=unit(point(side+'_Mid1')-point(side+'_Thumb1'))
 add(side+'_thumb',[move(side+'_Thumb1',thumbdir.cross(target),.45),move(side+'_Thumb2',flex,.45)],'hand')
add('torso_twist',[move('Spine01',up,.4)],'torso')
add('neck_turn',[move('Head',up,.6)],'neck')
add('both_shoulders',[move('L_Clavicle',front,.2),move('R_Clavicle',front,-.2),move('L_Upperarm',front,.6),move('R_Upperarm',front,-.6)],'shoulder')
add('reach',[move('R_Upperarm',front,-.55),move('R_Forearm',unit(point('R_Hand')-point('R_Forearm')).cross(front),.9)],'elbow')
def collision_count(vertices,tris,limit=2000):
 from mathutils.bvhtree import BVHTree
 from mathutils.geometry import intersect_ray_tri
 if not len(tris):return {'crossings':0,'candidates':0,'truncated':False}
 tree=BVHTree.FromPolygons([Vector(x) for x in vertices],tris.tolist(),all_triangles=True)
 pairs=[(a,b) for a,b in tree.overlap(tree) if a<b and not set(tris[a])&set(tris[b])];crossings=0
 for a,b in pairs[:limit]:
  ta=[Vector(vertices[i]) for i in tris[a]];tb=[Vector(vertices[i]) for i in tris[b]];hit=False
  for first,second in [(ta,tb),(tb,ta)]:
   for i in range(3):
    start=first[i];end=first[(i+1)%3];delta=end-start
    if delta.length<1e-10:continue
    p=intersect_ray_tri(*second,delta.normalized(),start,True)
    if p is not None and 1e-7<(p-start).dot(delta.normalized())<delta.length-1e-7:hit=True;break
   if hit:break
  crossings+=hit
 return {'crossings':crossings,'candidates':len(pairs),'truncated':len(pairs)>limit}
for plan in plans:
 reset();stats=[];issues=[]
 # Freeze each anatomical axis in its bone's rest frame before any ancestor
 # rotates. Compound FK must carry child axes with their parent, not hold them
 # fixed in world coordinates.
 for mv in plan['moves']:
  b=bones.get(mv['bone'])
  if b is not None:mv['local_axis_blender']=list((arm.matrix_world@b.matrix).to_quaternion().inverted()@Vector(mv['world_axis_blender']))
 # Local ROI for palm preservation and collision checks. Uses geometry, not weights.
 hand_roi={}
 if plan['region']=='hand':
  side=plan['name'][0];w=np.array(point(side+'_Hand'));m=np.array(point(side+'_Mid1'));long=m-w;length=float(np.linalg.norm(long));long/=max(length,1e-8)
  for o in meshes:
   co=rests[o.name];v=co-w;t=v@long;rad=np.linalg.norm(v-t[:,None]*long,axis=1)
   palm=(t>length*.05)&(t<length*.65)&(rad<length*.55)
   near=np.linalg.norm(v,axis=1)<max(length*2.7,height*.06)
   tri=triangles[o.name];roi_tris=tri[np.all(near[tri],axis=1)]
   hand_roi[o.name]=(palm,near,roi_tris,collision_count(co,roi_tris))
 for fraction in [.25,.5,1.0]:
  reset()
  for mv in plan['moves']:
   b=bones.get(mv['bone'])
   if b is None:issues.append('MISSING_BONE:'+mv['bone']);continue
   axis=Vector(mv['local_axis_blender']);b.rotation_mode='QUATERNION';b.rotation_quaternion=b.rotation_quaternion@Quaternion(axis,mv['angle']*fraction);bpy.context.view_layer.update()
  meshstats=[]
  for o in meshes:
   co=coords(o);rest=rests[o.name];disp=np.linalg.norm(co-rest,axis=1);e=edge_arrays[o.name];base=np.linalg.norm(rest[e[:,0]]-rest[e[:,1]],axis=1);good=base>height*1e-6;ratios=np.linalg.norm(co[e[good,0]]-co[e[good,1]],axis=1)/base[good]
   finite=bool(np.isfinite(co).all());stretch=float(ratios.max(initial=1));compression=float(ratios.min(initial=1));movement=float(disp.max(initial=0)/height)
   ms={'mesh':o.name,'finite':finite,'max_edge_stretch':stretch,'min_edge_ratio':compression,'max_displacement_relative_to_height':movement}
   center=np.array(point(plan['moves'][0]['bone']));roi=np.linalg.norm(rest-center,axis=1)<height*.055
   if int(roi.sum())>30:
    covariance=np.cov(rest[roi].T);eigen=np.linalg.eigvalsh(covariance)
    if eigen.min()>height*height*1e-8:
     volume_ratio=math.sqrt(max(float(np.linalg.det(np.cov(co[roi].T))),0)/max(float(np.linalg.det(covariance)),1e-30));ms['local_volume_proxy_ratio']=volume_ratio
     if volume_ratio<.5 or volume_ratio>2:issues.append('LOCAL_VOLUME_REVIEW:'+o.name)
   face=rest[:,2]>allcoords[:,2].min()+height*.85;fe=e[face[e].all(axis=1)];fb=np.linalg.norm(rest[fe[:,0]]-rest[fe[:,1]],axis=1);valid=fb>height*1e-6
   if valid.any():
    fr=np.linalg.norm(co[fe[valid,0]]-co[fe[valid,1]],axis=1)/fb[valid];distortion=float(np.quantile(np.abs(fr-1),.99));ms['face_shape_distortion_p99']=distortion
    if distortion>.03:issues.append('FACE_SHAPE_CHANGED:'+o.name)
   if not finite or stretch>10:issues.append('INVALID_OR_EXPLODING_MESH:'+o.name)
   elif stretch>2.5 or compression<.08:issues.append('LOCAL_STRETCH_OR_COLLAPSE:'+o.name)
   if plan['region']=='hand':
    palm,near,tris,baseline=hand_roi[o.name];palm_shift=float(disp[palm].max(initial=0)/height);leak=float(disp[~near].max(initial=0)/height);ms.update(palm_displacement_relative_to_height=palm_shift,outside_hand_displacement_relative_to_height=leak)
    if palm_shift>.005:issues.append('PALM_MOVES_WITH_FINGERS:'+o.name)
    if leak>.002:issues.append('FINGER_INFLUENCE_OUTSIDE_HAND:'+o.name)
    if fraction==1:
     collisions=collision_count(co,tris);ms['collisions']=collisions;ms['baseline_collisions']=baseline
     if collisions['truncated'] or collisions['crossings']>baseline['crossings']+3:issues.append('HAND_INTERSECTION_REVIEW:'+o.name)
   elif fraction==1 and plan['region']=='shoulder':
    near=np.linalg.norm(rest-center,axis=1)<height*.1;tri=triangles[o.name];tr=tri[near[tri].all(axis=1)];base_cross=collision_count(rest,tr);posed_cross=collision_count(co,tr);ms['shoulder_collisions']=posed_cross;ms['baseline_shoulder_collisions']=base_cross
    if posed_cross['truncated'] or posed_cross['crossings']>base_cross['crossings']+3:issues.append('SHOULDER_INTERSECTION_REVIEW:'+o.name)
   meshstats.append(ms)
  stats.append({'fraction':fraction,'meshes':meshstats})
 for mv in plan['moves']:
  x,y,z=mv['world_axis_blender'];mv['world_axis_gltf']=[x,z,-y]
 report['pose_plan'].append(plan)
 report['poses'].append({'name':plan['name'],'region':plan['region'],'verdict':'failed' if any(x.startswith('INVALID_OR_EXPLODING') or x.startswith('MISSING_BONE') for x in issues) else 'needs_review' if issues else 'passed','issues':sorted(set(issues)),'samples':stats})
reset();report['bones']=len(arm.data.bones);report['structure']='passed' if all(c['passed'] for c in report['checks']) else 'failed';report['deformation']='failed' if any(p['verdict']=='failed' for p in report['poses']) else 'needs_review' if any(p['verdict']=='needs_review' for p in report['poses']) else 'passed';report['verdict']='failed' if 'failed' in [report['structure'],report['deformation']] else 'needs_visual_review'
output.write_text(json.dumps(report,indent=2),encoding='utf8');output.with_suffix('.poses.json').write_text(json.dumps({'source_sha256':report['sha256'],'plans':report['pose_plan']},indent=2),encoding='utf8')
