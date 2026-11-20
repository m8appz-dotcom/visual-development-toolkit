"""Small local knowledge surface; no arbitrary filesystem path input."""
import json
from pathlib import Path
from typing import Literal

ROOT=Path(__file__).resolve().parent/'knowledge'
Topic=Literal['overview','guide','geometry','nodes','rig_animation','render','export','delivery','quick_api','identity_preservation']
STARTUP_NOTE='''
Blender agent workflow v2: Before producing an asset, call get_blender_workflow_docs(topic="overview") and load only the relevant recipe. The integrated guide covers framing/silhouette, lighting/materials, preview budgets and visual acceptance. Inspect capabilities and the actual target scene; batch coherent changes and validate evaluated data. Before defaulting to CPU for a render, inspect actual Cycles devices and measure a representative isolated job; do not assume GPU availability or persist preference changes. Use specific tools before arbitrary Python, durable jobs for long work, and copy transactions/checkpoints for reversible scene edits. Inspect final renders at delivery resolution; a thumbnail or successful script is not visual acceptance. Deliver 3D models in a tested interactive HTML viewer under the user's instructions. These recipes never override the user's brief, references, model/provider, access controls or image-processing restrictions. Load signatures from quick_api only when needed; do not load full decompiled/API dumps. Check version/preconditions and read actual output/errors before claiming success.

For identity-preserving character repairs, load identity_preservation, freeze the preferred base and original references with create_asset_preservation_guard, declare narrow edit regions and protected features, then validate candidate attributes, opacity, rig and texture pixels. Do not substitute generic eyes/features as a cleanup shortcut. Compare original/base/candidate visually; technical pass never establishes likeness. Use export_asset_with_preservation_guard for controlled delivery. The guard does not sandbox arbitrary Python or intercept other exporters.
'''

def register(mcp):
    @mcp.tool()
    def get_blender_workflow_docs(topic:Topic='overview')->dict[str,object]:
        """Read the integrated Blender guide, focused tested recipes or compact API; start with overview, load only the topic needed."""
        manifest=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
        if topic=='overview':
            return {'status':'ok','version':manifest['version'],'blender_build':manifest['blender_build'],
                    'topics':manifest['topics'],'workflow':['brief_and_references','inspect_target','shape_and_camera','lighting_and_materials','preview','final_visual_review','verify_consumer'],
                    'limits':['Recipes are scoped tested examples, not proof of every Blender feature','External effects are not rolled back by scene checkpoints','Budget suggestions require scene-specific measurement and visual review']}
        if topic=='guide':
            return {'status':'ok','version':manifest['version'],'text':(ROOT/'guide.md').read_text(encoding='utf-8')}
        if topic=='identity_preservation':
            return {'status':'ok','version':manifest['version'],'text':(ROOT/'identity-preservation.md').read_text(encoding='utf-8')}
        if topic=='quick_api':
            return {'status':'ok','reference':json.loads((ROOT/'quick-api.json').read_text(encoding='utf-8'))}
        return {'status':'ok','recipe':json.loads((ROOT/(topic+'.json')).read_text(encoding='utf-8'))}
