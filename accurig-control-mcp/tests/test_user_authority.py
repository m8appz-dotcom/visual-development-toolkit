import unittest,tempfile,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import base_gate as g
class UserAuthorityTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name);self.model=self.p/'source.fbx';self.model.write_bytes(b'synthetic fixture, not a real FBX')
  self.e=self.p/'message.txt';self.e.write_text('Synthetic explicit user authority, test only')
  self.a=self.p/'approval.json';self.r=self.p/'receipt.json';self.report=self.p/'review.json';self.report.write_text('{"status":"failed","findings":["synthetic open finding"]}')
  self.data={'actor':'user','status':'approved','source_sha256':g.sha(self.model),'scope':'base_model_accurig','decision_authority':'supersedes_reviewer_verdicts','message_reference':'synthetic-test-only','approval_text':'Synthetic test approval','evidence_path':str(self.e)};self.save()
 def tearDown(self):self.tmp.cleanup()
 def save(self):self.a.write_text(json.dumps(self.data))
 def approve(self):return g.approve_user(self.model,self.a,self.r,[self.report])
 def test_explicit_user_supersedes_rejected_review(self):
  before=self.report.read_bytes();self.approve();r=g.assert_gate(self.r,self.model);self.assertTrue(r['allowed']);self.assertEqual(r['authority'],'user');self.assertEqual(r['verdict'],'pass_warning');self.assertEqual(before,self.report.read_bytes());self.assertTrue(r['warnings'])
 def test_missing_reviewer_does_not_override_user(self):
  g.approve_user(self.model,self.a,self.r);self.assertTrue(g.assert_gate(self.r,self.model)['allowed'])
 def test_generic_approval_not_an_override(self):
  self.data.pop('decision_authority');self.save()
  with self.assertRaisesRegex(ValueError,'EXPLICIT_USER_AUTHORITY'):self.approve()
 def test_agent_cannot_be_user(self):
  self.data['actor']='agent';self.save()
  with self.assertRaisesRegex(ValueError,'USER_AUTHORITY_APPROVAL'):self.approve()
 def test_wrong_hash(self):
  self.data['source_sha256']='0'*64;self.save()
  with self.assertRaisesRegex(ValueError,'SOURCE_CHANGED'):self.approve()
 def test_modified_model_invalidates(self):
  self.approve();self.model.write_bytes(b'changed')
  with self.assertRaisesRegex(ValueError,'SOURCE_CHANGED'):g.assert_gate(self.r,self.model)
 def test_modified_message_invalidates(self):
  self.approve();self.e.write_text('changed')
  with self.assertRaisesRegex(ValueError,'EVIDENCE_CHANGED'):g.assert_gate(self.r,self.model)
 def test_modified_report_invalidates(self):
  self.approve();self.report.write_text('{}')
  with self.assertRaisesRegex(ValueError,'EVIDENCE_CHANGED'):g.assert_gate(self.r,self.model)
 def test_modified_approval_invalidates(self):
  self.approve();self.data['approval_text']='changed';self.save()
  with self.assertRaisesRegex(ValueError,'EVIDENCE_CHANGED'):g.assert_gate(self.r,self.model)
 def test_wrong_scope(self):
  self.data['scope']='all-future-models';self.save()
  with self.assertRaisesRegex(ValueError,'EXPLICIT_USER_AUTHORITY'):self.approve()
 def test_empty_evidence(self):
  self.e.write_text('')
  with self.assertRaisesRegex(ValueError,'REAL_USER_APPROVAL'):self.approve()
 def test_other_model_same_bytes_disallowed(self):
  self.approve();other=self.p/'other.fbx';other.write_bytes(self.model.read_bytes())
  with self.assertRaisesRegex(ValueError,'SOURCE_CHANGED'):g.assert_gate(self.r,other)
 def test_cannot_overwrite_model(self):
  with self.assertRaisesRegex(ValueError,'SEPARATE_AUTHORITY'):g.approve_user(self.model,self.a,self.model)
 def test_no_fabricated_pass_total(self):
  self.approve();r=g.read(self.r);r['verdict']='pass_total';g.save(self.r,r)
  with self.assertRaisesRegex(ValueError,'INVALID_USER_AUTHORITY'):g.assert_gate(self.r,self.model)
if __name__=='__main__':unittest.main()
