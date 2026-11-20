"""Pure contract checks for the Blender script, without importing Blender."""
import ast,pathlib,unittest
root=pathlib.Path(__file__).resolve().parents[1]
class ValidatorContract(unittest.TestCase):
 def test_detail_names_do_not_collide_with_check_arguments(self):
  tree=ast.parse((root/'scripts/validate_poses_v03.py').read_text(encoding='utf-8'));fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='check');report={'checks':[]};ns={'report':report};exec(compile(ast.Module(body=[fn],type_ignores=[]),'check','exec'),ns);ns['check']('weights',True,name='mesh',passed_detail='yes');self.assertEqual(report['checks'][0]['details']['name'],'mesh')
 def test_visual_acceptance_is_not_structural_verdict(self):
  text=(root/'scripts/validate_poses_v03.py').read_text(encoding='utf-8');self.assertIn("'visual':'pending'",text);self.assertIn("'ready_for_delivery':False",text);self.assertIn('for o in meshes:',text)
unittest.main()
