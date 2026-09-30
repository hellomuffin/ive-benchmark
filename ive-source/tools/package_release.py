"""Stage only the new IVE files; preserve unrelated website contents."""
from pathlib import Path
import shutil,zipfile,json,hashlib
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'site';TARGET=Path('/tmp/ive-release-standalone')
assert (TARGET/'.git').exists(), 'Expected isolated publishing repository'
episode=json.loads((SITE/'data/cooking.json').read_text())
example={'benchmark_version':'ive-v1','demo_only':True,
 'description':'One recorded demonstration, not a full benchmark submission.',
 'model':{'name':episode['model'],'family':'Frontier API','revision':'recorded-demo-'+episode['sourceHash'][:12]},
 'runs':[{'engine':'cooksim','run_id':1,'episodes':[{'case_id':'b3_hard_nops_medium_map_1','persona_id':'classic_expert',
 'trace_uri':'data/cooking.json','trace_sha256':hashlib.sha256((SITE/'data/cooking.json').read_bytes()).hexdigest()}]}]}
(SITE/'submission/example.json').write_text(json.dumps(example,indent=2)+'\n')
def copy_tree(src,dst,skip=()):
 for p in src.rglob('*'):
  if not p.is_file() or any(x in p.parts for x in skip) or p.suffix=='.pyc':continue
  if p.suffix=='.wav':continue
  target=dst/p.relative_to(src);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
kit=SITE/'ive-preview-kit.zip'
with zipfile.ZipFile(kit,'w',zipfile.ZIP_DEFLATED,compresslevel=4) as z:
 for p in SITE.rglob('*'):
  if p.is_file() and p!=kit and p.suffix!='.wav':z.write(p,Path('ive-preview/site')/p.relative_to(SITE))
 z.write(ROOT/'README.md','ive-preview/README.md')
 for p in (ROOT/'tools').glob('*.py'):z.write(p,Path('ive-preview/tools')/p.name)
copy_tree(SITE,TARGET/'docs',skip=('__pycache__',))
copy_tree(ROOT/'tools',TARGET/'ive-source/tools',skip=('__pycache__',))
(TARGET/'ive-source').mkdir(exist_ok=True)
readme=(ROOT/'README.md').read_text().replace('--directory site','--directory docs').replace('python tools/','python ive-source/tools/').replace('--traces site','--traces docs').replace(' site/submission/',' docs/submission/')
(TARGET/'ive-source/README.md').write_text(readme)
(TARGET/'README.md').write_text(readme)
(TARGET/'docs/.nojekyll').touch()
(TARGET/'ive-submissions').mkdir(exist_ok=True)
shutil.copy2(ROOT/'SUBMIT.md',TARGET/'ive-submissions/README.md')
(TARGET/'.github/workflows').mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/'submission-workflow.yml',TARGET/'.github/workflows/ive-submissions.yml')
print('Staged website, replay kit, source, and submission workflow without changing existing pages.')
