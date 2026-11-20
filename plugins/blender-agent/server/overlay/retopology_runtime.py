"""Executed by the existing Blender bridge. No caller-provided Python is accepted."""
import hashlib
import importlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

KEY = 'codex_retopology_adapter'


def context():
    value = bpy.app.driver_namespace.get(KEY)
    if not value:
        raise ValueError('No retopology project. Call begin_retopology first.')
    return value


def instance(required=True):
    module = sys.modules.get('retopoflow.retopoflow.retopoflow')
    rf = module.RetopoFlow.instance if module else None
    if required and (rf is None or not hasattr(rf, 'rftarget') or not hasattr(rf, 'rftools') or not getattr(rf, 'rftool', None)):
        raise ValueError('RetopoFlow is not ready. Inspect the session after its modal startup completes.')
    return rf


def topology(obj, bme=None):
    verts = bme.verts if bme is not None else obj.data.vertices
    faces = bme.faces if bme is not None else obj.data.polygons
    report = {'object': obj.name, 'vertices': len(verts), 'faces': len(faces),
            'quads': sum(len(f.verts if bme is not None else f.vertices) == 4 for f in faces),
            'finite': all(math.isfinite(x) for v in verts for x in v.co)}
    import bmesh
    temporary = bme is None
    mesh = bme
    if temporary:
        mesh = bmesh.new()
        mesh.from_mesh(obj.data)
    try:
        report.update(edges=len(mesh.edges), boundary_edges=sum(e.is_boundary for e in mesh.edges),
                      nonmanifold_junction_edges=sum(len(e.link_faces)>2 for e in mesh.edges),
                      zero_area_faces=sum(f.calc_area()<1e-16 for f in mesh.faces))
    finally:
        if temporary:
            mesh.free()
    return report


def inspect():
    ctx = bpy.app.driver_namespace.get(KEY)
    rf = instance(False)
    value = {'status': 'ok', 'version': bpy.app.version_string,
             'background': bpy.app.background, 'filepath': bpy.data.filepath,
             'modal_active': rf is not None, 'ready': rf is not None and hasattr(rf, 'rftarget') and hasattr(rf, 'rftools') and bool(getattr(rf, 'rftool', None))}
    if ctx:
        value.update(project={k: ctx[k] for k in ['source', 'target', 'output', 'source_sha256', 'published']})
        value['source_topology'] = topology(bpy.data.objects[ctx['source']])
        target = bpy.data.objects.get(ctx['target'])
        if target:
            value['target_topology'] = topology(target, rf.rftarget.bme if value['ready'] else None)
    if value['ready']:
        value['tools'] = [t.name for t in rf.rftools]
        value['selected_tool'] = rf.rftool.name
    return value


def begin(o):
    if bpy.app.background or bpy.app.driver_namespace.get(KEY):
        raise ValueError('Use a fresh owned interactive session')
    addon = Path(o['addon'])
    existing = sys.modules.get('retopoflow')
    if existing and Path(existing.__file__).resolve() != (addon/'__init__.py').resolve():
        raise ValueError('A different RetopoFlow package is already loaded in this session')
    sys.path.insert(0, str(addon.parent))
    package = importlib.import_module('retopoflow')
    if not existing:
        package.register()
    br = importlib.import_module('retopoflow.retopoflow.blenderregister')
    if not br.import_succeeded:
        raise RuntimeError('RetopoFlow import failed; inspect Blender log')
    with bpy.data.libraries.load(o['source'], link=False) as (available, loaded):
        if o['source_object'] not in available.objects:
            raise ValueError('Requested source object does not exist')
        # Remove factory objects before append, avoiding collisions such as
        # source Cube becoming Cube.001 in an otherwise clean test session.
        for obj in list(bpy.context.scene.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        loaded.objects = available.objects
        loaded.actions = available.actions
    # Appending clears fake-user protection on otherwise unused actions.
    # Preserve the source library in the NEW file, not only the active action.
    for action in loaded.actions:
        if action:
            action.use_fake_user = True
    action_names = [a.name for a in loaded.actions if a]
    # Fresh owned session only. Appended references are copies, never linked data.
    incoming = {obj for obj in loaded.objects if obj}
    for obj in list(bpy.context.scene.objects):
        if obj not in incoming:
            bpy.data.objects.remove(obj, do_unlink=True)
    for obj in incoming:
        bpy.context.scene.collection.objects.link(obj)
        obj.select_set(False)
    source = bpy.data.objects.get(o['source_object'])
    if not source or source not in incoming or source.type != 'MESH':
        raise ValueError('Source must be an appended mesh with an unambiguous name')
    modifiers = []
    rigs = []
    for obj in incoming:
        if obj.type == 'ARMATURE':
            rigs.append((obj.name, obj.data.pose_position, obj.hide_get()))
            obj.data.pose_position = 'REST'
            obj.hide_set(True)
    for mod in source.modifiers:
        if mod.type == 'ARMATURE':
            modifiers.append((mod.name, mod.show_viewport))
            mod.show_viewport = False
    source.hide_set(False)
    source.select_set(True)
    bpy.context.view_layer.objects.active = source
    bpy.context.scene.frame_set(1)
    rig_transforms = {obj.name:[list(row) for row in source.matrix_world.inverted() @ obj.matrix_world]
                      for obj in incoming if obj.type == 'ARMATURE'}
    bpy.ops.wm.save_as_mainfile(filepath=o['stage'])
    area = next((a for a in bpy.context.screen.areas if a.type == 'VIEW_3D'), None)
    if area is None:
        raise ValueError('No VIEW_3D area available')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    with bpy.context.temp_override(window=bpy.context.window, area=area, region=region):
        outcome = bpy.ops.cgcookie.retopoflow_newtarget_active('INVOKE_DEFAULT')
    target = bpy.context.view_layer.objects.active
    if target == source or target.type != 'MESH':
        raise RuntimeError('RetopoFlow did not create its target')
    for mod in target.modifiers:
        if mod.type == 'MIRROR':
            mod.use_axis = (False, False, False)
    bpy.app.driver_namespace[KEY] = {
        'source': source.name, 'target': target.name, 'output': o['output'],
        'source_file': o['source'], 'source_sha256': o['source_sha256'],
        'stage': o['stage'], 'modifiers': modifiers, 'rigs': rigs,
        'rig_transforms': rig_transforms,
        'source_actions': action_names,
        'published': False, 'weights_transferred': False,
    }
    return {'status': 'ok', 'startup': list(outcome), 'source': source.name,
            'target': target.name, 'addon_version': list(package.bl_info['version']),
            'next': 'inspect_retopology until ready=true'}


def add_patch(o):
    rf = instance()
    ctx = context()
    source = bpy.data.objects[ctx['source']]
    from retopoflow.addon_common.common.maths import Point
    projected = []
    distances = []
    for xyz in o['vertices']:
        point = Vector(xyz)
        hit, normal, _, _ = rf.nearest_sources_Point(Point(source.matrix_world @ point))
        if hit is None or normal is None:
            raise ValueError('RetopoFlow source projection missed')
        local_hit = source.matrix_world.inverted() @ Vector(hit)
        distance = (local_hit-point).length
        if distance > o['max_projection_distance']:
            raise ValueError('Projection exceeds source-local tolerance; no geometry was changed')
        projected.append((hit, normal))
        distances.append(distance)
    for face in o['faces']:
        a,b,c = (Vector(projected[i][0]) for i in face[:3])
        if (b-a).cross(c-a).length_squared < 1e-24:
            raise ValueError('Projected face has zero area; no geometry was changed')
    target = rf.rftarget
    # Lazy custom layers must exist before acquiring BMVert references.
    _ = target.layer_pin
    rf.undo_push('MCP add patch')
    target.rewrap()
    backup = target.bme.copy()
    try:
        verts = [target.new_vert(p,n) for p,n in projected]
        for face in o['faces']:
            rf.new_face([verts[i] for i in face])
        target.bme.normal_update()
        target.dirty()
        target.clean()
    except Exception:
        target.bme.free()
        target.bme = backup
        target.rewrap()
        target.dirty()
        target.clean()
        raise
    else:
        backup.free()
    return {'status':'ok','added_vertices':len(verts),'added_faces':len(o['faces']),
            'max_projection_distance':max(distances), 'topology':topology(target.obj,target.bme),
            'method':'native RetopoFlow projection and mesh creation; caller-directed layout'}


def bone_strip(o):
    instance()
    ctx = context()
    source = bpy.data.objects[ctx['source']]
    rig = bpy.data.objects.get(o['rig'])
    if rig is None or rig.type != 'ARMATURE':
        raise ValueError('Existing rig object required')
    source_vertices=[v.co.copy() for v in source.data.vertices]
    source_faces=[list(f.vertices) for f in source.data.polygons]
    bvh=BVHTree.FromPolygons(source_vertices,source_faces)
    vertices=[]
    # RetopoFlow normalizes source object scale during editing, but does not
    # change its mesh coordinates. Use captured pre-normalization transforms.
    from mathutils import Matrix
    if rig.name not in ctx['rig_transforms']:
        raise ValueError('Rig must belong to the copied source project')
    rig_to_source = Matrix(ctx['rig_transforms'][rig.name])
    for ring in o['rings']:
        bone=rig.data.bones.get(ring['bone'])
        if bone is None:
            raise ValueError('Unknown bone: '+ring['bone'])
        # World normalization scales only the source object. The original rig
        # and source transforms were captured by begin before modal startup.
        center=rig_to_source @ bone.head_local.lerp(bone.tail_local,ring['t'])
        axis=(rig_to_source.to_3x3() @ (bone.tail_local-bone.head_local)).normalized()
        reference=Vector((0,1,0)) if abs(axis.y)<.9 else Vector((1,0,0))
        radial=axis.cross(reference).normalized()
        radial2=axis.cross(radial).normalized()
        for j in range(o['sides']):
            angle=2*math.pi*j/o['sides']
            direction=radial*math.cos(angle)+radial2*math.sin(angle)
            hit,normal,_,distance=bvh.ray_cast(center,direction,o['max_radius'])
            if hit is None:
                raise ValueError('Bone strip ray missed within maximum radius; no geometry was changed')
            vertices.append(list(hit))
    faces=[]
    n=o['sides']
    for i in range(len(o['rings'])-1):
        for j in range(n):
            faces.append([i*n+j,i*n+(j+1)%n,(i+1)*n+(j+1)%n,(i+1)*n+j])
    return add_patch({'vertices':vertices,'faces':faces,'max_projection_distance':o['max_radius']*.01})


def select_tool(o):
    rf=instance()
    tool=next((t for t in rf.rftools if t.name==o['tool']),None)
    if tool is None:
        raise ValueError('Unknown tool; available: '+', '.join(t.name for t in rf.rftools))
    rf.select_rftool(tool)
    return {'status':'ok','selected_tool':rf.rftool.name,'strokes_simulated':False}


def relax(o):
    rf=instance()
    target=rf.rftarget
    from retopoflow.addon_common.common.maths import Point
    _ = target.layer_pin
    rf.undo_push('MCP projected relaxation')
    target.rewrap()
    backup=target.bme.copy()
    moved=0
    try:
        for _ in range(o['iterations']):
            updates=[]
            for v in target.bme.verts:
                if not v.link_edges or (o['preserve_boundary'] and v.is_boundary) or v[target.layer_pin]:
                    continue
                adjacent=[e.other_vert(v).co for e in v.link_edges]
                local=v.co.lerp(sum(adjacent,Vector())/len(adjacent),o['strength'])
                hit,normal,_,_=rf.nearest_sources_Point(Point(target.obj.matrix_world @ local))
                if hit is None:
                    raise ValueError('Projection missed during relaxation')
                updates.append((v,target.obj.matrix_world.inverted() @ Vector(hit)))
            for v,p in updates:
                v.co=p
            moved+=len(updates)
        target.bme.normal_update()
        target.dirty(); target.clean()
    except Exception:
        target.bme.free(); target.bme=backup; target.rewrap(); target.dirty(); target.clean()
        raise
    else:
        backup.free()
    return {'status':'ok','iterations':o['iterations'],'vertex_updates':moved,
            'method':'adapter Laplacian relaxation + native RetopoFlow projection; not native Relax brush'}


def finish(o):
    rf=instance()
    ctx=context()
    if not o['cancel'] and not len(rf.rftarget.bme.faces):
        raise ValueError('Cannot commit an empty target')
    rf.done(cancel=o['cancel'])
    ctx['cancelled']=o['cancel']
    return {'status':'ok','commit_requested':not o['cancel'],'next':'Inspect until modal_active=false'}


def undo(o):
    rf=instance()
    if not o['redo'] and not rf.undo_stack_actions():
        raise ValueError('No RetopoFlow undo state available')
    if o['redo']:
        rf.redo_pop()
    else:
        rf.undo_pop()
    rf.rftarget.dirty();rf.rftarget.clean()
    return {'status':'ok','redo':o['redo'],'topology':topology(rf.rftarget.obj,rf.rftarget.bme)}


def finished():
    ctx=context()
    if instance(False) is not None:
        raise ValueError('Finish RetopoFlow and wait for modal exit before this operation')
    if ctx.get('cancelled'):
        raise ValueError('Retopology was cancelled')
    source=bpy.data.objects[ctx['source']]
    target=bpy.data.objects[ctx['target']]
    if bpy.context.mode != 'OBJECT':
        if bpy.context.edit_object != target:
            raise ValueError('A different object is being edited; restore its mode explicitly')
        bpy.ops.object.mode_set(mode='OBJECT')
    for name,enabled in ctx['modifiers']:
        source.modifiers[name].show_viewport=enabled
    for name,pose,hidden in ctx['rigs']:
        rig=bpy.data.objects[name]
        rig.data.pose_position=pose
        rig.hide_set(hidden)
    return ctx,source,target


def barycentric(point,a,b,c):
    v0,v1,v2=b-a,c-a,point-a
    aa,ab,bb,pa,pb=v0.dot(v0),v0.dot(v1),v1.dot(v1),v2.dot(v0),v2.dot(v1)
    den=aa*bb-ab*ab
    if abs(den)<1e-24:
        raise ValueError('Degenerate source triangle')
    v,w=(bb*pa-ab*pb)/den,(aa*pb-ab*pa)/den
    values=[max(0,x) for x in (1-v-w,v,w)]
    return [x/sum(values) for x in values]


def transfer_weights(o):
    ctx,source,target=finished()
    rig=bpy.data.objects.get(o['rig'])
    if rig is None or rig.type!='ARMATURE':
        raise ValueError('Existing rig object required')
    source.data.calc_loop_triangles()
    triangles=[list(t.vertices) for t in source.data.loop_triangles]
    verts=[v.co.copy() for v in source.data.vertices]
    bvh=BVHTree.FromPolygons(verts,triangles,all_triangles=True)
    matrix=source.matrix_world.inverted() @ target.matrix_world
    transferred=[]
    max_distance=0
    for v in target.data.vertices:
        hit,_,fi,distance=bvh.find_nearest(matrix @ v.co)
        factors=barycentric(hit,*(verts[i] for i in triangles[fi]))
        weights={}
        for i,factor in zip(triangles[fi],factors):
            for g in source.data.vertices[i].groups:
                weights[g.group]=weights.get(g.group,0)+g.weight*factor
        total=sum(weights.values())
        if total<1e-8:
            raise ValueError('Source has unweighted geometry; target was not changed')
        transferred.append({source.vertex_groups[i].name:w/total for i,w in weights.items() if w>1e-8})
        max_distance=max(max_distance,distance)
    if target.vertex_groups:
        raise ValueError('Target already has groups; refusing to overwrite existing skin weights')
    mod=None
    try:
        for group in source.vertex_groups:
            target.vertex_groups.new(name=group.name)
        for i,weights in enumerate(transferred):
            for name,weight in weights.items():
                target.vertex_groups[name].add([i],weight,'REPLACE')
        mod=target.modifiers.new('Retopology transferred skin','ARMATURE')
        mod.object=rig
        srcmod=next((m for m in source.modifiers if m.type=='ARMATURE'),None)
        if srcmod:
            mod.use_deform_preserve_volume=srcmod.use_deform_preserve_volume
    except Exception:
        target.vertex_groups.clear()
        if mod is not None:
            target.modifiers.remove(mod)
        raise
    ctx['weights_transferred']=True
    return {'status':'ok','vertices':len(transferred),'groups':len(target.vertex_groups),
            'max_transfer_distance_source_units':max_distance,'rig':rig.name,
            'method':'nearest source triangle + barycentric interpolation + normalization'}


def validate_poses(o):
    ctx,source,target=finished()
    if not ctx['weights_transferred']:
        raise ValueError('Transfer weights before comparing deformation')
    rig=bpy.data.objects.get(o['rig'])
    if rig is None or rig.type!='ARMATURE':
        raise ValueError('Existing rig required')
    for pose in o['poses']:
        if pose['action'] and pose['action'] not in bpy.data.actions:
            raise ValueError('Unknown action: '+pose['action'])
    animation=rig.animation_data_create()
    original_action=animation.action
    original_slot=animation.action_slot
    original_frame=bpy.context.scene.frame_current
    original_subframe=bpy.context.scene.frame_subframe
    original_pose=rig.data.pose_position
    original_matrices={b.name:b.matrix_basis.copy() for b in rig.pose.bones}
    original_mutes=[(t,t.mute) for t in animation.nla_tracks]
    rows=[]
    try:
        rig.data.pose_position='POSE'
        for track,_ in original_mutes:
            track.mute=True
        for pose in o['poses']:
            action=bpy.data.actions.get(pose['action']) if pose['action'] else None
            animation.action=action
            if action and action.slots:
                animation.action_slot=action.slots[0]
            for bone in rig.pose.bones:
                bone.matrix_basis.identity()
            bpy.context.scene.frame_set(pose['frame'])
            bpy.context.view_layer.update()
            deps=bpy.context.evaluated_depsgraph_get()
            so,to=source.evaluated_get(deps),target.evaluated_get(deps)
            sm,tm=so.to_mesh(),to.to_mesh()
            try:
                sm.calc_loop_triangles()
                sv=[source.matrix_world @ v.co for v in sm.vertices]
                faces=[list(t.vertices) for t in sm.loop_triangles]
                bvh=BVHTree.FromPolygons(sv,faces,all_triangles=True)
                tv=[target.matrix_world @ v.co for v in tm.vertices]
                probes=tv+[sum((tv[i] for i in f.vertices),Vector())/len(f.vertices) for f in tm.polygons]
                step=max(1,math.ceil(len(probes)/o['sample_limit']))
                probes=probes[::step]
                ds=[bvh.find_nearest(p)[3] for p in probes]
                scale=bpy.context.scene.unit_settings.scale_length*1000
                rows.append({'action':pose['action'],'frame':pose['frame'],'probes':len(probes),
                             'finite':all(math.isfinite(x) for p in tv for x in p),
                             'mean_distance_mm':sum(ds)/len(ds)*scale,'max_distance_mm':max(ds)*scale})
            finally:
                so.to_mesh_clear();to.to_mesh_clear()
    finally:
        animation.action=original_action
        if original_action and original_slot:
            animation.action_slot=original_slot
        for track,mute in original_mutes:
            track.mute=mute
        rig.data.pose_position=original_pose
        bpy.context.scene.frame_set(original_frame,subframe=original_subframe)
        for name,matrix in original_matrices.items():
            rig.pose.bones[name].matrix_basis=matrix
        bpy.context.view_layer.update()
    ctx['pose_validation']=rows
    return {'status':'ok','poses':rows,'state_restored':True,
            'scope':'sampled one-way surface distance; not visual approval or full animation coverage'}


def save():
    ctx,source,target=finished()
    output=Path(ctx['output'])
    if output.exists() or ctx['published']:
        raise ValueError('Output already exists or project was published; refusing overwrite')
    digest=hashlib.sha256(Path(ctx['source_file']).read_bytes()).hexdigest()
    if digest!=ctx['source_sha256']:
        raise ValueError('Source changed externally; no output published')
    if any(name not in bpy.data.actions or not bpy.data.actions[name].use_fake_user for name in ctx['source_actions']):
        raise ValueError('Source animation library is not preserved; no output published')
    output.parent.mkdir(parents=True,exist_ok=True)
    # Save to a private staging file then publish without replacing anything.
    import uuid
    stage=output.with_name('.retopology-'+uuid.uuid4().hex+'.blend')
    bpy.ops.wm.save_as_mainfile(filepath=str(stage),copy=True)
    import os
    os.link(stage,output)
    stage.unlink()
    ctx['published']=True
    return {'status':'ok','output_path':str(output),'bytes':output.stat().st_size,
            'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'source_unchanged':True,
            'preserved_actions':len(ctx['source_actions']),
            'topology':topology(target)}


def dispatch(o):
    handlers={'inspect':lambda _:inspect(),'begin':begin,'add_patch':add_patch,
              'bone_strip':bone_strip,'select_tool':select_tool,'relax':relax,
              'finish':finish,'transfer_weights':transfer_weights,
              'undo':undo,
              'validate_poses':validate_poses,'save':lambda _:save()}
    handler=handlers.get(o['operation'])
    if handler is None:
        raise ValueError('Unsupported retopology operation')
    return handler(o)


result=dispatch(OPTIONS)
