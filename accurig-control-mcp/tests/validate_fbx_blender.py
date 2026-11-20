"""Executed only in a separate background Blender process via Blender MCP."""
import bpy,json,pathlib,math
ROOT=pathlib.Path('D:/visual-development-toolkit/accurig-control-mcp')
source=ROOT/'outputs/Pete-rigged-run5.fbx'
before=set(bpy.data.objects)
import_result=bpy.ops.import_scene.fbx(filepath=str(source))
created=[o for o in bpy.data.objects if o not in before]
arms=[o for o in created if o.type=='ARMATURE']
meshes=[o for o in created if o.type=='MESH']
report={'source':str(source),'import_result':sorted(import_result),'armatures':[{'name':a.name,'bones':len(a.data.bones)} for a in arms],'meshes':[]}
for mesh in meshes:
 bone_names={b.name for a in arms for b in a.data.bones}
 bone_group_ids={g.index for g in mesh.vertex_groups if g.name in bone_names}
 weighted=sum(any(g.group in bone_group_ids and g.weight>0 for g in v.groups) for v in mesh.data.vertices)
 report['meshes'].append({'name':mesh.name,'vertices':len(mesh.data.vertices),'polygons':len(mesh.data.polygons),'weighted_vertices':weighted,'bone_groups':len(bone_group_ids),'armature_modifiers':sum(m.type=='ARMATURE' and m.object in arms for m in mesh.modifiers)})
assert 'FINISHED' in import_result and arms and meshes
assert all(m['weighted_vertices']==m['vertices'] and m['armature_modifiers'] for m in report['meshes'])
arm=arms[0];bone=next(b for b in arm.pose.bones if b.name.endswith('L_Upperarm'))
mesh=max(meshes,key=lambda m:len(m.data.vertices));samples=list(range(0,len(mesh.data.vertices),max(1,len(mesh.data.vertices)//3000)))
def sample():
 bpy.context.view_layer.update()
 evaluated=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
 return [evaluated.data.vertices[i].co.copy() for i in samples]
initial=sample();saved=bone.matrix_basis.copy();bone.rotation_mode='XYZ';bone.rotation_euler.z+=.45
posed=sample();delta=max((a-b).length for a,b in zip(initial,posed));bone.matrix_basis=saved
report['pose_test']={'bone':bone.name,'maximum_sample_displacement':delta,'samples':len(samples)}
assert math.isfinite(delta) and delta>1e-5
report['passed']=True
(ROOT/'reports/fbx-independent-validation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
result=report
