"""Independent validation of real GLB/FBX in an isolated Blender process."""
import bpy,sys,json,pathlib,math,hashlib
from mathutils import Quaternion
source,output=sys.argv[sys.argv.index('--')+1:]
source=pathlib.Path(source);output=pathlib.Path(output)
before=set(bpy.data.objects)
if source.suffix.lower()=='.fbx':bpy.ops.import_scene.fbx(filepath=str(source))
else:bpy.ops.import_scene.gltf(filepath=str(source))
objects=[o for o in bpy.data.objects if o not in before];arms=[o for o in objects if o.type=='ARMATURE'];helpers={b.custom_shape for a in arms for b in a.pose.bones if b.custom_shape};meshes=[o for o in objects if o.type=='MESH' and o not in helpers]
report={'source':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'excluded_bone_display_helpers':[o.name for o in helpers],'checks':[],'meshes':[],'poses':[],'limitations':['Pose tests cover the listed rotations only. Visual/anatomical inspection remains necessary.','Stretch thresholds are conservative engineering screens, not a calibrated anatomical quality score.']}
def check(check_name,passed,**details):report['checks'].append({'name':check_name,'passed':bool(passed),'details':details})
check('armature_and_mesh',bool(arms and meshes))
if not arms or not meshes:raise RuntimeError('No imported armature or mesh')
arm=arms[0];bone_names={b.name for b in arm.data.bones}
check('finite_bind_transforms',all(math.isfinite(v) for b in arm.data.bones for row in b.matrix_local for v in row))
height=max(max((o.matrix_world@v.co).z for o in meshes for v in o.data.vertices)-min((o.matrix_world@v.co).z for o in meshes for v in o.data.vertices),1e-8)
for mesh in meshes:
 ids={g.index for g in mesh.vertex_groups if g.name in bone_names};unweighted=0;bad_sums=0;nonfinite=0
 for v in mesh.data.vertices:
  weights=[g.weight for g in v.groups if g.group in ids];s=sum(weights)
  unweighted+=s<=1e-8;bad_sums+=abs(s-1)>.002;nonfinite+=any(not math.isfinite(w) or w<0 for w in weights) or any(not math.isfinite(c) for c in v.co)
 mods=sum(m.type=='ARMATURE' and m.object==arm for m in mesh.modifiers)
 info={'name':mesh.name,'vertices':len(mesh.data.vertices),'unweighted':unweighted,'bad_weight_sums':bad_sums,'nonfinite_or_negative':nonfinite,'armature_modifiers':mods};report['meshes'].append(info)
 check('weights:'+mesh.name,not(unweighted or bad_sums or nonfinite) and bool(mods),**info)
mesh=max(meshes,key=lambda o:len(o.data.vertices));indices=list(range(0,len(mesh.data.vertices),max(1,len(mesh.data.vertices)//4000)))
edges=list(mesh.data.edges)[::max(1,len(mesh.data.edges)//4000)]
def coords():
 bpy.context.view_layer.update();o=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());return [v.co.copy() for v in o.data.vertices]
rest=coords();saved={b.name:(b.rotation_mode,b.matrix_basis.copy()) for b in arm.pose.bones}
specs=[('left_shoulder','L_Upperarm','Z',.65),('right_shoulder','R_Upperarm','Z',-.65),('left_elbow','L_Forearm','Z',.9),('right_elbow','R_Forearm','Z',-.9),('left_hip','L_Thigh','X',.6),('right_hip','R_Thigh','X',.6),('left_knee','L_Calf','X',-.9),('right_knee','R_Calf','X',-.9),('torso_twist','Spine01','Y',.35),('left_wrist','L_Hand','Z',.45),('right_wrist','R_Hand','Z',-.45),('left_finger','L_Index1','Z',.7),('right_finger','R_Index1','Z',-.7)]
for label,suffix,axis,angle in specs:
 for b in arm.pose.bones:b.rotation_mode=saved[b.name][0];b.matrix_basis=saved[b.name][1]
 bone=next((b for b in arm.pose.bones if b.name==suffix or b.name.endswith('_'+suffix)),None)
 if bone is None:report['poses'].append({'name':label,'verdict':'needs_review','reason':'bone not found: '+suffix});continue
 bone.rotation_mode='QUATERNION';bone.rotation_quaternion=bone.rotation_quaternion@Quaternion({'X':(1,0,0),'Y':(0,1,0),'Z':(0,0,1)}[axis],angle)
 posed=coords();displacements=[(posed[i]-rest[i]).length for i in indices];ratios=[]
 for e in edges:
  a,b=e.vertices;baseline=(rest[a]-rest[b]).length
  if baseline>height*1e-6:ratios.append((posed[a]-posed[b]).length/baseline)
 maximum=max(displacements);stretch=max(ratios,default=1);finite=all(math.isfinite(c) for p in posed for c in p)
 verdict='failed' if not finite or maximum<=height*1e-7 or stretch>10 else 'needs_review' if stretch>2.5 else 'passed'
 report['poses'].append({'name':label,'bone':bone.name,'axis':axis,'radians':angle,'verdict':verdict,'max_displacement_relative_to_height':maximum/height,'sampled_max_edge_stretch':stretch,'finite':finite})
for b in arm.pose.bones:b.rotation_mode=saved[b.name][0];b.matrix_basis=saved[b.name][1]
report['bones']=len(arm.data.bones);report['verdict']='failed' if any(not c['passed'] for c in report['checks']) or any(p['verdict']=='failed' for p in report['poses']) else 'needs_review' if any(p['verdict']=='needs_review' for p in report['poses']) else 'passed'
output.write_text(json.dumps(report,indent=2),encoding='utf8')
result=report
