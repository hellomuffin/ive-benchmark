"""Read-only release audit. Never export credentials, local datasets, or binaries."""
from pathlib import Path
import hashlib,json,re,subprocess
ROOT=Path(__file__).resolve().parents[1];WS=ROOT.parent
SOURCES={
 'cooksim':('cook-bench-engine',['cooksim','web/js','web/css','web/vendor','web/assets','examples'],['pyproject.toml','README.md']),
 'screensim':('screensim',['screensim','examples'],['pyproject.toml','README.md']),
 'vhhome':('vh-streaming-engine',['tools'],['README.md','Dockerfile.vhsim'])}
secret=re.compile(r'sk-proj-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{20,}|AIza[A-Za-z0-9_-]{25,}')
machine=re.compile(r'/(?:weka|home|opt/conda)/[^\s\"\']+')
report={}
for engine,(folder,dirs,files) in SOURCES.items():
 base=WS/folder
 candidates=[]
 for sub in dirs:
  for p in (base/sub).rglob('*'):
   if not p.is_file() or p.is_symlink() or any(x in p.parts for x in ['tmp','__pycache__','.git','node_modules']):continue
   if p.suffix in {'.py','.js','.json','.html','.css','.toml','.glb','.gltf','.png','.svg','.jpg'}:candidates.append(p)
 candidates.extend(base/f for f in files if (base/f).is_file())
 findings=[];inventory=[]
 for p in sorted(set(candidates)):
  rel=str(p.relative_to(base));content=p.read_bytes();inventory.append({'path':rel,'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()})
  if p.suffix in {'.py','.js','.json','.html','.css','.md','.toml'}:
   text=content.decode('utf8',errors='replace')
   if secret.search(text):findings.append({'path':rel,'issue':'credential-pattern-match','publish':False})
   if machine.search(text):findings.append({'path':rel,'issue':'machine-specific-path','publish':'review'})
 licenses=[str(p.relative_to(base)) for p in base.glob('*LICENSE*')]
 revision=subprocess.run(['git','-C',str(base),'rev-parse','HEAD'],capture_output=True,text=True).stdout.strip()
 report[engine]={'revision':revision,'rootLicenses':licenses,'candidateFiles':len(inventory),'candidateBytes':sum(x['bytes'] for x in inventory),'findings':findings,'inventory':inventory,'status':'audit only; not packaged or published'}
upstream=WS/'vh-streaming-engine/virtualhome_repo/LICENSE'
report['vhhome']['upstreamLicense']={'path':'virtualhome_repo/LICENSE','heading':upstream.read_text().splitlines()[0],'note':'This identifies the Python repository license; it is not a redistribution determination for Unity binaries or all assets.'}
out=ROOT/'.work/engine-release-audit.json';out.parent.mkdir(exist_ok=True);out.write_text(json.dumps(report,indent=2))
for key,r in report.items():print(key,r['candidateFiles'],'candidate files;',len(r['findings']),'review findings; root license present:',bool(r['rootLicenses']))
