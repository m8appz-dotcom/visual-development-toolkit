import bpy
rd=bpy.context.scene.render
attrs=[(rd,'filepath'),(rd,'resolution_x'),(rd,'resolution_y'),(rd,'resolution_percentage'),(rd.image_settings,'file_format')]
if hasattr(bpy.context.scene,'cycles'):
    attrs.append((bpy.context.scene.cycles,'samples'))
backup=[(obj,key,getattr(obj,key)) for obj,key in attrs]
try:
    rd.filepath=OPTIONS['output']
    rd.image_settings.file_format=OPTIONS['format']
    if OPTIONS['thumbnail']:
        scale=min(1,320/max(rd.resolution_x,rd.resolution_y))
        rd.resolution_x=max(1,round(rd.resolution_x*scale))
        rd.resolution_y=max(1,round(rd.resolution_y*scale))
        rd.resolution_percentage=100
        if rd.engine=='CYCLES':
            bpy.context.scene.cycles.samples=min(bpy.context.scene.cycles.samples,16)
    returned=bpy.ops.render.render(write_still=True)
    if 'FINISHED' not in returned:
        raise RuntimeError('Render operator did not finish: '+repr(returned))
    result={'engine':rd.engine,'width':rd.resolution_x*rd.resolution_percentage//100,'height':rd.resolution_y*rd.resolution_percentage//100,'settings_restored_on_return':True}
finally:
    for obj,key,value in reversed(backup):
        setattr(obj,key,value)
