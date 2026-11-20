import bpy

def run_with_context(options):
    selected = list(bpy.context.selected_objects)
    active = bpy.context.view_layer.objects.active
    previous_mode = active.mode if active else 'OBJECT'
    target = bpy.data.objects.get(options['object_name']) if options['object_name'] else active
    if options['object_name'] and target is None:
        raise ValueError('Object does not exist: ' + options['object_name'])
    kwargs = {}
    if options['area_type']:
        if bpy.app.background:
            raise RuntimeError('This operation requires an interactive Blender session')
        found = next(((w,a,r) for w in bpy.context.window_manager.windows for a in w.screen.areas if a.type == options['area_type'] for r in a.regions if r.type == 'WINDOW'), None)
        if not found:
            raise RuntimeError('Requested area/region is not available')
        kwargs.update(window=found[0], area=found[1], region=found[2])
    try:
        if bpy.context.object and bpy.context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        for obj in bpy.context.selected_objects:
            obj.select_set(False)
        if target:
            target.select_set(True)
            bpy.context.view_layer.objects.active = target
        with bpy.context.temp_override(**kwargs):
            if options['mode']:
                bpy.ops.object.mode_set(mode=options['mode'])
            module, name = options['identifier'].split('.')
            operation = getattr(getattr(bpy.ops, module), name)
            if not operation.poll():
                raise RuntimeError('Operator poll rejected the supplied context: ' + options['identifier'])
            returned = operation(**options['properties'])
            if 'FINISHED' not in returned:
                raise RuntimeError('Operator did not finish: ' + repr(returned))
            bpy.context.view_layer.update()
            return {'operator': options['identifier'], 'returned': sorted(returned), 'active_object': target.name if target else None}
    finally:
        if bpy.context.object and bpy.context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        for obj in bpy.context.selected_objects:
            obj.select_set(False)
        for obj in selected:
            if bpy.data.objects.get(obj.name) is obj:
                obj.select_set(True)
        if active and bpy.data.objects.get(active.name) is active:
            bpy.context.view_layer.objects.active = active
            if previous_mode != 'OBJECT':
                bpy.ops.object.mode_set(mode=previous_mode)

result = run_with_context(OPTIONS)
