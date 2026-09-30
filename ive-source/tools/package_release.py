"""Stage only the new IVE files; preserve unrelated website contents."""
from pathlib import Path
import shutil,zipfile
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'site';TARGET=Path('/tmp/ive-release-standalone')
assert (TARGET/'.git').exists(), 'Expected isolated publishing repository'
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
(TARGET/'ive-source').mkdir(exist_ok=True);shutil.copy2(ROOT/'README.md',TARGET/'ive-source/README.md')
(TARGET/'README.md').write_text((ROOT/'README.md').read_text().replace('--directory site','--directory docs'))
(TARGET/'docs/.nojekyll').touch()
(TARGET/'ive-submissions').mkdir(exist_ok=True)
shutil.copy2(ROOT/'SUBMIT.md',TARGET/'ive-submissions/README.md')
(TARGET/'.github/workflows').mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/'submission-workflow.yml',TARGET/'.github/workflows/ive-submissions.yml')
print('Staged website, replay kit, source, and submission workflow without changing existing pages.')
