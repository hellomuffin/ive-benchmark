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
 def test_malformed_types(self):
  for x in [None, [], 7, 'not an object']:
   self.assertTrue(validate(x))
  for field in ['engine','run_id']:
   d=self.sample();d['runs'][0][field]=[];self.assertTrue(validate(d))
  for field in ['case_id','persona_id','trace_uri','trace_sha256']:
   d=self.sample();d['runs'][0]['episodes'][0][field]=[];self.assertTrue(validate(d))
 def test_full_valid(self):
  d=self.sample();prototype=d['runs'][0]['episodes'][0];d['runs']=[]
  for engine,n in {'cooksim':150,'vhhome':75,'screensim':90}.items():
   for run in [1,2,3]:d['runs'].append({'engine':engine,'run_id':run,'episodes':[dict(prototype,case_id=str(i)) for i in range(n)]})
  self.assertEqual(validate(d,full=True),[])
  d['runs'][-1]['episodes'][-1]['case_id']='mismatched-case'
  self.assertTrue(validate(d,full=True))
 def test_demo_is_not_full(self):
  d=self.sample();d['demo_only']=True;self.assertTrue(validate(d,full=True))
 def test_catalog_membership(self):
  c={'engines':{'cooksim':[{'case_id':'one','persona_id':'baseline'}]}}
  d=self.sample();self.assertEqual(validate(d,catalog=c),[])
  d['runs'][0]['episodes'][0]['case_id']='not-in-benchmark'
  self.assertTrue(validate(d,catalog=c))

class ManifestBuilderTests(unittest.TestCase):
 def test_complete_manifest_and_missing_trace(self):
  from create_manifest import build
  from validate_submission import load_catalog
  import tempfile
  catalog=load_catalog()
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)
   for engine,cells in catalog['engines'].items():
    for run in [1,2,3]:
     folder=root/engine/f'run-{run}';folder.mkdir(parents=True)
     for cell in cells:
      file=folder/f'{cell["case_id"]}__{cell["persona_id"]}.json'
      file.write_text('{"test_fixture":true}')
   result=build(root,'Test fixture','Frontier API','test',catalog)
   self.assertEqual(sum(len(r['episodes']) for r in result['runs']),945)
   self.assertEqual(validate(result,root=root,full=True,catalog=catalog),[])
   file.unlink()
   with self.assertRaisesRegex(ValueError,'1 missing traces'):build(root,'Test fixture','Frontier API','test',catalog)

if __name__=='__main__':unittest.main()
