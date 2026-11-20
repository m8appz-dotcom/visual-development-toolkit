"""Record actual partial rejection and package the private source update."""
from pathlib import Path
import hashlib,json,zipfile,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from external_review import PROMPT,validate,sha

rdir=ROOT/'reports/gemini-browser-20261024'
source=Path('C:/ActiveProjects-X-20261023/ChatGPT/3d personajes/nico-kenneth-97-animado/preparacion-manos-cuello-20261024/web/candidate.glb')
expected='2b8c7bde626729814d928eadd9ecbbd6f4509943af52e6748efb1327f8b9e95f'
assert sha(source)==expected,'Displayed candidate changed; cannot bind historical screenshot'
attachment=Path('C:/Users/kenny/AppData/Local/Temp/codex-clipboard-8d2b3681-2d49-4a5a-b08e-cdd3f2503fb7.png')
(rdir/'prompt.txt').write_text(PROMPT,encoding='utf8')
report={'schema':'gemini-browser-review/1','source_sha256':expected,'provider':'Gemini','transport':'browser',
        'reviewer_id':'gemini-browser-da4654f72ff4591a','account_verified':True,'account':'fitvfat@gmail.com',
        'model_selection':{'selected':'3.8 Flash','available_flash_models':['3.8 Flash'],'latest_available_verified':True},
        'session_url':'https://gemini.google.com/app/da4654f72ff4591a',
        'selector_evidence':str(rdir/'selector.png'),'response_evidence':str(rdir/'response.png'),
        'prompt_path':str(rdir/'prompt.txt'),'raw_response_path':str(rdir/'response.txt'),
        'reviewed_images':{str(attachment):sha(attachment)},'status':'failed',
        'findings':[{'status':'open','location':'visible wrist and distal forearm','observation':'Abrupt visible narrowing and volume discontinuity at the wrist.'}],
        'limitations':['Partial screenshot only; palm, opposite hand and full body not observed.',
                      'Gemini inferred rig/skinning and UV causes from a static screenshot; these causes are unverified. This candidate is static and has no rig.'],
        'scope':'Actual browser review of user-provided screenshot; sufficient to reject, never to approve the full character.'}
path=rdir/'external-review.json';path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
result=validate(str(path),expected,{},set(),'codex-implementer',require_approval=False)
assert result['blockers']
(rdir/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')

pipeline=Path('D:/visual-development-toolkit/kenneth-character-pipeline')
files=['plugin.json','.codex-plugin/plugin.json','skills/3d-preservation/SKILL.md',
       'skills/3d-preservation/references/base-model-filter.md','skills/3d-preservation/references/external-visual-review.md',
       'skills/3d-preservation/scripts/base_gate.py','skills/3d-preservation/scripts/external_review.py',
       'tests/test_base_gate.py','tests/test_external_review.py']
archive=ROOT/'reports/kenneth-character-pipeline-0.3.4-browser-review.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for rel in files:z.write(pipeline/rel,rel)
with zipfile.ZipFile(archive) as z:
 assert set(z.namelist())==set(files) and z.testzip() is None
print(json.dumps({'source_verified':True,'partial_external_review':'failed','archive':str(archive),'files':len(files)}))
