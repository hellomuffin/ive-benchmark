import hashlib,json,tempfile,unittest
from pathlib import Path
from validate_submission import validate

class SubmissionTests(unittest.TestCase):
 def sample(self):
  return {'benchmark_version':'ive-v1','model':{'name':'Test','family':'Frontier API','revision':'test-only'},'runs':[{'engine':'cooksim','run_id':1,'episodes':[{'case_id':'one','persona_id':'baseline','trace_uri':'one.json','trace_sha256':hashlib.sha256(b'{}').hexdigest()}]}]}
 def test_partial_structure(self):self.assertEqual(validate(self.sample()),[])
 def test_full_requires_all_runs(self):self.assertTrue(validate(self.sample(),full=True))
 def test_duplicates(self):
  d=self.sample();d['runs']*=2;self.assertTrue(validate(d))
 def test_hash(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);(p/'one.json').write_text('{}');self.assertEqual(validate(self.sample(),p),[])
   (p/'one.json').write_text('{"changed":true}');self.assertTrue(validate(self.sample(),p))
 def test_path_escape(self):
  d=self.sample();d['runs'][0]['episodes'][0]['trace_uri']='../outside.json';self.assertTrue(validate(d,Path('/tmp/example')))
 def test_empty(self):self.assertTrue(validate({}))

if __name__=='__main__':unittest.main()
