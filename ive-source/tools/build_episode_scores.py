"""Attach the paper's engine metrics to selected episodes, using official scorers."""
import json,os,sys,subprocess,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];WS=ROOT.parent;SITE=ROOT/'site'
GROUPS={'cooksim':['cooking','cooking-peer','persona-classic_novice','persona-baseline','persona-classic_expert'],
        'vhhome':['household','household-peer'],'screensim':['mobile','mobile-peer']}
REPOS={'cooksim':'cook-bench-engine','vhhome':'vh-streaming-engine','screensim':'screensim'}

def run(engine):
 repo=WS/REPOS[engine];sys.path[:0]=[str(repo/'tools'),str(repo)];os.chdir(repo)
 if engine=='cooksim':
  os.environ['COOKSIM_CASES']='bench/v5/cases_composite_v5.json'
  import build_formal_results_page as scorer
  cells,recipes,refs,allow,n=scorer.tables();scorer_file=repo/'tools/eval_v2_sweep.py'
 elif engine=='vhhome':
  import dump_experiments_vh as scorer
  scorer_file=repo/'tools/assist_metrics.py'
 else:
  import dump_experiments as scorer
  scorer_file=repo/'tools/dump_experiments.py'
 for key in GROUPS[engine]:
  path=SITE/f'data/{key}.json';e=json.loads(path.read_text());source=WS/e['source']
  if engine=='screensim':
   case='app_privacy_quarantine__c2';persona='speed_demon'
   r=next(json.loads(l) for l in source.open() if json.loads(l).get('episode')==case and json.loads(l).get('persona')==persona)
   s=scorer.score(r);cap=2*scorer.ref_ticks(r['task'])+8
   metrics={'inTimeSuccess':bool(s['in_time']),'budget':cap,'detected':s['tp'],'triggered':s['fired']}
   e.update(run=2,case=case,personaId=persona)
  else:
   r=json.loads(source.read_text())
   if engine=='cooksim':
    case=source.stem;cell=cells[case]
    s=scorer.EV.score_episode(r,'/'.join(source.parts[-4:])[:-5],refs[cell],recipes[cell],{},{},n_err_planned=n[case],allowance=allow[case])
    metrics={'inTimeSuccess':bool(s['v3']['in_time_success']),'budget':s['v3']['cap_ticks'],'detected':s['v3']['tp'],'triggered':s['evidence']['errors_fired']}
   else:
    reference=scorer.MEASURED[r['scenario']];scorer.AM.t_ref=lambda _case:reference
    s=scorer.AM.episode_metrics(r)
    metrics={'inTimeSuccess':bool(s['S']),'budget':s['C'],'detected':s['tp'],'triggered':s['fired']}
  metrics['scorer']=str(scorer_file.relative_to(WS));metrics['scorerSha256']=hashlib.sha256(scorer_file.read_bytes()).hexdigest()
  e['metrics']=metrics;path.write_text(json.dumps(e,ensure_ascii=False,indent=2)+'\n')
  print(key,metrics,flush=True)

if __name__=='__main__':
 if len(sys.argv)>1:run(sys.argv[1])
 else:
  for engine in GROUPS:subprocess.run([sys.executable,str(Path(__file__).resolve()),engine],check=True)
