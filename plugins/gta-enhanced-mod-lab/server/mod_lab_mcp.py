from __future__ import annotations
import sys
sys.dont_write_bytecode=True
import importlib.metadata,json
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from common import CONFIG,PLUGIN_ROOT,STATE,digest
from install_ledger import apply_install,list_plans,plan_install,rollback_install
from test_runner import audit,reconcile_runtime,runtime_preflight,runtime_stock_test,static_suite
from package_inspection import field_notes,inspect_package,review_script_source,rebuild_package

mcp=FastMCP('GTA Enhanced Mod Lab',instructions='Local GTA Enhanced asset checks and scoped file plans. Static passes do not certify gameplay. Installation defaults to the staging sandbox. Never bypass the existing QA coordinator or shared lease.')
READ=ToolAnnotations(readOnlyHint=True,destructiveHint=False,openWorldHint=False)
WRITE=ToolAnnotations(readOnlyHint=False,destructiveHint=False,openWorldHint=False)

@mcp.tool(annotations=READ)
def mod_lab_status()->dict:
 """Check installed local dependencies and supported file/runtime scopes."""
 paths={'dotnet':CONFIG['dotnet'],'native_auditor':CONFIG['audit_dll'],'game_root':CONFIG['game_root'],'lab_root':CONFIG['lab_root']}
 paths['package_auditor']=CONFIG['package_audit_dll']
 paths['rpf_rebuild']=CONFIG['rpf_rebuild_dll']
 paths['rpf_shader_data']=str(Path(CONFIG['rpf_rebuild_dll']).with_name('ShadersGen9Conversion.xml'))
 return {'plugin':'gta-enhanced-mod-lab','version':'0.4.4','plugin_root':str(PLUGIN_ROOT),'mcp_sdk':importlib.metadata.version('mcp'),'dependencies':{k:{'path':v,'available':Path(v).exists()} for k,v in paths.items()},'state_root':str(STATE),'allowed_install_roots':CONFIG['allowed_install_roots'],'tools':['test_runner','installation_ledger','package_inspection','source_review','dlc_rebuild'],'gameplay_certified':False}

@mcp.tool(annotations=READ)
def read_modding_guide()->dict:
 """Read the researched GTA Enhanced guide shipped with this plugin."""
 path=PLUGIN_ROOT/'skills/gta-enhanced-workflow/references/GUIA-GTA-ENHANCED.md'
 return {'guide':path.read_text(encoding='utf-8'),'sha256':digest(path)}

@mcp.tool(annotations=READ)
def read_mod_field_notes()->dict:
 """Read package, franchise and rig/animation QA findings with hashes and explicit compatibility limits."""
 return field_notes()

@mcp.tool(annotations=WRITE)
def inspect_mod_package(folder:str)->dict:
 """Inspect extracted DLC RPF containers, map references, MLO rooms/portals and vehicle metadata; never install."""
 return inspect_package(folder)

@mcp.tool(annotations=WRITE)
def rebuild_mod_package(folder:str,converted_resources:str)->dict:
 """Rebuild fresh DLC copies from converted resources; verify every leaf payload and fragment rigs/geometry/collisions. Never install or port scripts."""
 return rebuild_package(folder,converted_resources)

@mcp.tool(annotations=WRITE)
def review_mod_script_source(folder:str)->dict:
 """Flag C#/Lua review patterns in authorized source copies; heuristics do not certify safety."""
 return review_script_source(folder)

@mcp.tool(annotations=WRITE)
def audit_mod_assets(folder:str)->dict:
 """Read native assets within configured roots and save a fresh structural report."""
 return audit(folder)

@mcp.tool(annotations=WRITE)
def convert_mod_assets(folder:str)->dict:
 """Create a Gen9 copy in a new run folder; never overwrite input or install it."""
 return audit(folder,True)

@mcp.tool(annotations=WRITE)
def run_static_mod_tests()->dict:
 """Run real asset readback, preservation checks and three negative fixtures."""
 return static_suite()

@mcp.tool(annotations=READ)
async def runtime_test_preflight()->dict:
 """Inspect the existing local FiveM QA baseline without launching or connecting."""
 return await runtime_preflight()

@mcp.tool(annotations=WRITE)
async def run_runtime_stock_test(case:str='stock_smoke')->dict:
 """Run the existing stock NPC case only on a verified, ready baseline with a shared lease."""
 return await runtime_stock_test(case)

@mcp.tool(annotations=WRITE)
async def reconcile_runtime_test(operation_id:str)->dict:
 """Resolve a recorded uncertain QA result without replaying its action."""
 return await reconcile_runtime(operation_id)

@mcp.tool(annotations=WRITE)
def plan_mod_install(source_folder:str,target_folder:str,relative_paths:list[str])->dict:
 """Create a hashed file plan inside configured scope; do not apply it."""
 return plan_install(source_folder,target_folder,relative_paths)

@mcp.tool(annotations=WRITE)
def apply_mod_install(plan_id:str,expected_plan_sha256:str)->dict:
 """Apply one reviewed plan with original backups and hash checks."""
 return apply_install(plan_id,expected_plan_sha256)

@mcp.tool(annotations=WRITE)
def rollback_mod_install(plan_id:str)->dict:
 """Restore the plan's originals; refuse to overwrite independent changes."""
 return rollback_install(plan_id)

@mcp.tool(annotations=READ)
def list_mod_install_plans()->dict:
 """Read the most recent durable installation journal entries."""
 return list_plans()

def main():mcp.run(transport='stdio')
if __name__=='__main__':main()
