from pathlib import Path
r=Path(__file__).resolve().parents[1]
p=r/'src/accurig.mjs';s=p.read_text(encoding='utf-8')
a=s.index("  const log=await fs.open(ROOT+'/reports/application.log','a');")
b=s.index("  let targets;",a)
s=s[:a]+'''  const launched=JSON.parse(await new Promise((resolve,reject)=>cp.execFile('D:/visual-development-toolkit/windows/venv/Scripts/python.exe',[ROOT+'/scripts/launch_detached.py',String(mainPort),String(rendererPort)],{windowsHide:true},(e,out)=>e?reject(e):resolve(out))));
  this.child={pid:launched.pid};this.identity={pid:launched.pid,executable:EXE,main_port:mainPort,renderer_port:rendererPort,owned:true,launch_mode:launched.launch_mode};await fs.writeFile(ROOT+'/data/session.json',JSON.stringify(this.identity,null,2));
'''+s[b:]
p.write_text(s,encoding='utf-8')
p=r/'src/server.mjs';s=p.read_text(encoding='utf-8').replace("version:'0.2.0'","version:'0.3.0'")
s=s.replace("const tools=[",'''const tools=[
 ['accurig_review_joints','Record source/revision-bound multi-view joint review. Hard anatomy errors block acceptance.',{expected_revision:z.number().int(),joints_sha256:z.string().regex(/^[a-f0-9]{64}$/),verdict:z.enum(['accepted','requires_corrections']),views:z.array(z.enum(['front','left','right','back','hands'])).min(4),observations:z.string().min(10),resolved_warnings:z.array(z.string()).default([])},a=>core.reviewJoints(a),false],
 ['accurig_record_visual_review','Record actual visual inspection of the exact validated generation, all test poses and affected views. Open defects block ready_for_delivery.',{generation_id:z.string().regex(/^[a-f0-9]{32}$/),preview_sha256:z.string().regex(/^[a-f0-9]{64}$/),verdict:z.enum(['accepted','requires_corrections']),views:z.array(z.string()).min(5),poses:z.array(z.string()).min(1),observations:z.string().min(10),open_defects:z.array(z.string()).default([])},a=>core.recordVisual(a),false],
 ['accurig_delete_generation','Permanently delete only a proven owned inactive generation explicitly identified twice. Verifies actor and every extra GLB copy; preserves original inputs and other histories.',{generation_id:z.string().regex(/^[a-f0-9]{32}$/),confirm_generation_id:z.string().regex(/^[a-f0-9]{32}$/),extra_paths:z.array(z.string()).default([])},a=>core.deleteGeneration(a),false],''')
s=s.replace("avatar:z.enum(['auto','original','calibrated']).default('auto')","avatar:z.enum(['original','calibrated']).default('original')")
p.write_text(s,encoding='utf-8')
