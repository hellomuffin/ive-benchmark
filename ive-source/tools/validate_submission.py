"""Validate an IVE manifest and its local episode traces. No model calls or uploads."""
import argparse,hashlib,json
from pathlib import Path
ENGINES={'cooksim':150,'vhhome':75,'screensim':90}
FAMILIES={'Frontier API','Streaming API','Open non-streaming','Open streaming'}
def validate(data,root=None,full=False):
 errors=[]
 def require(ok,msg):
  if not ok:errors.append(msg)
 require(data.get('benchmark_version')=='ive-v1','benchmark_version must be ive-v1')
 model=data.get('model',{})
 require(isinstance(model,dict),'model must be an object')
 if isinstance(model,dict):
  for key in ['name','revision']:require(isinstance(model.get(key),str) and bool(model[key].strip()),f'model.{key} is required')
  require(model.get('family') in FAMILIES,'Unknown model family')
 runs=data.get('runs',[]);require(isinstance(runs,list) and bool(runs),'runs must be a nonempty array')
 seen=set()
 if not isinstance(runs,list):return errors
 for i,run in enumerate(runs):
  label=f'run {i+1}'
  if not isinstance(run,dict):errors.append(f'{label}: must be an object');continue
  engine=run.get('engine');rid=run.get('run_id');key=(engine,rid)
  require(engine in ENGINES,f'{label}: unknown engine')
  require(type(rid)==int and rid>0,f'{label}: run_id must be a positive integer')
  require(key not in seen,f'{label}: duplicate engine/run');seen.add(key)
  episodes=run.get('episodes',[]);require(isinstance(episodes,list) and bool(episodes),f'{label}: episodes must be a nonempty array')
  if not isinstance(episodes,list):continue
  if full and engine in ENGINES:require(len(episodes)==ENGINES[engine],f'{label}: expected {ENGINES[engine]} episodes, found {len(episodes)}')
  pairs=set()
  for j,ep in enumerate(episodes):
   el=f'{label}, episode {j+1}'
   if not isinstance(ep,dict):errors.append(f'{el}: must be an object');continue
   for field in ['case_id','persona_id','trace_uri','trace_sha256']:require(isinstance(ep.get(field),str) and bool(ep[field]),f'{el}: missing {field}')
   pair=(ep.get('case_id'),ep.get('persona_id'));require(pair not in pairs,f'{el}: duplicate case/persona');pairs.add(pair)
   sha=ep.get('trace_sha256','');require(len(sha)==64 and all(c in '0123456789abcdef' for c in sha),f'{el}: invalid SHA-256')
   if root and ep.get('trace_uri'):
    target=(root/ep['trace_uri']).resolve()
    if not target.is_relative_to(root.resolve()):errors.append(f'{el}: trace path escapes submission directory');continue
    if not target.is_file():errors.append(f'{el}: trace missing');continue
    require(hashlib.sha256(target.read_bytes()).hexdigest()==sha,f'{el}: trace hash mismatch')
    try:
     trace=json.loads(target.read_text());require(isinstance(trace,dict),f'{el}: trace is not a JSON object')
    except (ValueError,UnicodeError):errors.append(f'{el}: trace is not valid JSON')
 if full:require(seen=={(e,r) for e in ENGINES for r in [1,2,3]},'Full submissions require all three environments and runs 1, 2, 3')
 return errors
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path);p.add_argument('--traces',type=Path);p.add_argument('--full',action='store_true');a=p.parse_args()
 try:errors=validate(json.loads(a.manifest.read_text()),a.traces,a.full)
 except (ValueError,OSError) as e:errors=[str(e)]
 if errors:print('\n'.join('ERROR: '+e for e in errors));raise SystemExit(1)
 print('Manifest validation passed. Scores and trace authenticity still require benchmark verification.')
