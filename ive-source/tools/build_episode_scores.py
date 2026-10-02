"""Attach the paper's engine metrics to selected episodes, using official scorers."""
import json,os,sys,subprocess,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];WS=ROOT.parent;SITE=ROOT/'site'
GROUPS={'cooksim':['cooking','cooking-peer','persona-classic_novice','persona-baseline','persona-classic_expert','cooking-fire','cooking-wrong'],
        'vhhome':['household','household-peer','household-timeout','household-stalled'],'screensim':['mobile','mobile-peer','mobile-success','mobile-failure']}
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
   case=e.get('case','app_privacy_quarantine__c2');persona=e.get('personaId','speed_demon')
   r=next(json.loads(l) for l in source.open() if json.loads(l).get('episode')==case and json.loads(l).get('persona')==persona)
   s=scorer.score(r);cap=2*scorer.ref_ticks(r['task'])+8
   metrics={'inTimeSuccess':bool(s['in_time']),'budget':cap,'referenceTicks':scorer.ref_ticks(r['task']),'detected':s['tp'],'triggered':s['fired']}
   e.update(run=2,case=case,personaId=persona)
  else:
   r=json.loads(source.read_text())
   if engine=='cooksim':
    case=source.stem;cell=cells[case]
    s=scorer.EV.score_episode(r,'/'.join(source.parts[-4:])[:-5],refs[cell],recipes[cell],{},{},n_err_planned=n[case],allowance=allow[case])
    metrics={'inTimeSuccess':bool(s['v3']['in_time_success']),'budget':s['v3']['cap_ticks'],'referenceTicks':refs[cell],'detected':s['v3']['tp'],'triggered':s['evidence']['errors_fired']}
   else:
    reference=scorer.MEASURED[r['scenario']];scorer.AM.t_ref=lambda _case:reference
    s=scorer.AM.episode_metrics(r)
    metrics={'inTimeSuccess':bool(s['S']),'budget':s['C'],'referenceTicks':reference,'detected':s['tp'],'triggered':s['fired']}
    # Mirror the official flag regrading for the live event annotations as well.
    phases=[p for p in r.get('phases',[]) if p.get('dev_live') is not None]
    rank={'valid':0,'valid_alias':1,'early_correct':2,'early_alias':3,'late':4,'early':5,'wrong_name':6,'invalid_label':7}
    seen=set();detected={}
    for turn in r.get('conversation',[]):
     if turn.get('speaker')!='vlm':continue
     flag=(turn.get('vlm_json') or {}).get('flag')
     name=str((flag.get('error') or '') if isinstance(flag,dict) else flag or '').strip()
     if not name or name in seen:continue
     seen.add(name);tick=turn['t'];candidates=[]
     for i,p in enumerate(phases):
      lo=(p.get('window') or [10**9])[0]
      verdict=scorer.AM.P.verdict_of({'err':p['err'],'dev':p['dev_live'],'window':(lo,10**9)},name,tick)
      candidates.append((rank.get(verdict,99),0 if lo<=tick else 1,i,verdict))
     if not candidates:continue
     _,_,i,verdict=min(candidates)
     if verdict in scorer.AM.P.ARMS_DETECTION or verdict in scorer.AM.P.ARMS_PREVENTION:detected.setdefault(i,tick)
    for event in e.get('events',[]):
     i=next((i for i,p in enumerate(phases) if p['injected_at']==event['tick']),None)
     if i is None:continue
     event['detected']=i in detected
     event['detectedAt']=detected.get(i)
     event.pop('detectionTimeUnknown',None)
  metrics['scorer']=str(scorer_file.relative_to(WS));metrics['scorerSha256']=hashlib.sha256(scorer_file.read_bytes()).hexdigest()
  e['metrics']=metrics;path.write_text(json.dumps(e,ensure_ascii=False,indent=2)+'\n')
  print(key,metrics,flush=True)

if __name__=='__main__':
 if len(sys.argv)>1:run(sys.argv[1])
 else:
  for engine in GROUPS:subprocess.run([sys.executable,str(Path(__file__).resolve()),engine],check=True)
