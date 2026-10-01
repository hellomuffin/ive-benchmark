"""Matched recorded episodes. Export only public trajectory fields, never prompts.

Run before build_comparison_media.py. Assertions enforce shared task/event settings.
"""
import json
from pathlib import Path
from build_data import common, quality, digest, dump, WORKSPACE as WS, ROOT, PUBLIC as SITE

MODELS={'gpt-6-astra':'GPT-6 Astra','gemini-3.8-flash':'Gemini 3.8 Flash',
        'gemini-3.1-pro-preview':'Gemini 3.1 Pro'}
PERSONAS={'classic_expert':'Independent expert','classic_novice':'Guidance-seeking novice','baseline':'Balanced user'}
ERRORS={'serve_raw':'Plate an uncooked ingredient','forget_next_step':'Pause instead of continuing',
 'repeat_step':'Repeat an ingredient step','omit_subgoal':'Skip a recipe step'}

def load(path): return json.loads((WS/path).read_text())
def conversation(r):
 return [{'tick':c['t'],'speaker':'assistant' if c['speaker']=='vlm' else 'user','text':c['text']}
         for c in r['conversation'] if c.get('text','').strip()]
def save(e):
 path=SITE/f'data/{e["id"]}.json'
 if path.exists():
  old=json.loads(path.read_text())
  if old.get('sourceHash')==e['sourceHash']:
   for k in ['frameCount','playback','presentation','metrics']:
    if k in old:e[k]=old[k]
   lookup={(d['tick'],d['speaker'],d['text']):d for d in old['dialogue']}
   for d in e['dialogue']:
    for k in ['audio','duration','start']:
     if k in lookup.get((d['tick'],d['speaker'],d['text']),{}):d[k]=lookup[(d['tick'],d['speaker'],d['text'])][k]
 if not (SITE/f'assets/media/{e["id"]}.mp4').exists():
  e.pop('media',None);e.pop('poster',None)
 dump(path,e)
 return e

def cook(key,model,persona,case):
 path=f'cook-bench-engine/tmp/formal_v5/frames/{persona}/{model}/{case}.json';r=load(path)
 p=r['persona_v2'];levels={'low':1,'medium':2,'high':3}
 axes=[levels[p['skill']],levels[p['trust']],p['q1'],p['q2'],p['q3']]
 task=('Cook and serve a Fish & Chips Platter: cooked fish followed by two portions of cooked potato.' if 'hard_nops' in case
       else 'Prepare a Loaded Burrito: tortilla, cooked rice, cooked steak, chopped tomato, and chopped lettuce, plated in this order.')
 e=common(key,'CookSim',MODELS[model],PERSONAS[persona],axes,task,r,path)
 e.update(case=case,personaId=persona,run=1,ticks=r['ticks'],completed=r['outcome']=='won',outcome=r['outcome'],
          dialogue=conversation(r),actions=[{'start':a['t_issue'],'end':a.get('t_done') or a['t_issue'],'text':a['cmd']} for a in r['actions']],
          crops={'main':[522,26,520,370],'context':[0,26,520,370]})
 e['events']=[]
 for inj in r['injections']:
  k=inj.get('report_keys',{});t=k.get('injected_at')
  if t is None:continue
  fam=inj['family'];label=ERRORS.get(inj['err'],{'qa_probe':'Temporal question','qa_proactive':'Request a readiness alert','plan_change':'Add fresh lettuce'}.get(fam,fam))
  e['events'].append({'label':label,'kind':fam,'tick':t,'detail':(inj.get('qa') or {}).get('question_as_asked',''),
    'end':k.get('released_at',inj.get('archived_at',t)), 'detected':bool(inj.get('flagged_valid')),
    'detectedAt':inj.get('detected_at') or inj.get('cook_detected_at'), 'prevented':bool(inj.get('prevented')),
    'answeredAt':(inj.get('qa') or {}).get('answered_at'),'alertAt':(inj.get('proactive') or {}).get('alert_t')})
 # Successful preparation/assembly operations are taken from the engine record.
 final_build=max((v['build'] for v in r['plate_seq']),default=0)
 e['milestones']=[{'label':f"Plate {v['state']} {v['item']}",'tick':v['t']} for v in r['plate_seq'] if v['build']==final_build]
 if e['completed']:e['milestones'].append({'label':'Serve','tick':r['ticks']})
 e['quality']=quality(path.replace('/frames/','/sq_v4/frames/'),e['dialogue'])
 e['detection']={'detected':sum(x['detected'] for x in e['events'] if x['kind']=='error'),'triggered':sum(x['kind']=='error' for x in e['events'])}
 return save(e),r

def vh():
 model='gpt-6-astra';case='cx_tidybedroom_stall_place';persona='safety_stepper'
 path=f'vh-streaming-engine/tmp/bench_v1/{model}/{model}__{case}__{persona}.json';r=load(path)
 e=common('household-peer','VHSim',MODELS[model],'Cautious collaborator',[2,3,1,3,1],
 'Tidy the bedroom: return the book to the desk, close the cabinet, turn off the lamp, and bring the mug to the kitchen table.',r,path)
 e.update(case=case,personaId=persona,run=1,ticks=r['ticks'],completed=r['outcome']=='won',outcome=r['outcome'],dialogue=conversation(r),
 actions=[{'start':a['t_issue'],'end':a.get('t_done') or a['t_issue'],'text':a['cmd']} for a in r['action_log']],
 crops={'main':[0,24,640,456],'context':[640,24,480,456]})
 e['milestones']=[]
 for cmd,label in [('put the book on the desk','Book on desk'),('close the cabinet','Cabinet closed'),('switch off the tablelamp','Lamp off'),('put the mug on the kitchentable','Mug on table')]:
  actions=[a for a in r['action_log'] if a['cmd']==cmd and a['status']=='done']
  assert actions,cmd
  e['milestones'].append({'label':label,'tick':actions[-1]['t_done']})
 e['events']=[{'label':'Pause while holding the book' if p['err']=='stall' else 'Put the mug on the wrong surface',
 'kind':'error','tick':p['injected_at'],'end':p['released_at'],'detected':p.get('caught',False),
 'detectedAt':next((f['t'] for f in p.get('flags',[]) if f.get('verdict')=='valid'),None)} for p in r['phases']]
 e['quality']=quality(path.replace(f'/{model}/',f'/sq_v4/{model}/'),e['dialogue'])
 e['detection']={'detected':sum(x['detected'] for x in e['events']),'triggered':len(e['events'])}
 return save(e),r

def screen():
 model='gpt-6-astra';path=f'screensim/tmp/bench_v2/{model}.records.jsonl'
 r=next(json.loads(l) for l in (WS/path).open() if json.loads(l).get('episode')=='app_privacy_quarantine__c2' and json.loads(l).get('persona')=='speed_demon')
 dump(ROOT/'.work/mobile-peer-record.json',r)
 e=common('mobile-peer','ScreenSim',MODELS[model],'Hurried, skeptical user',[2,1,3,2,3],
 'Stop TripSnap from accessing location, tracking activity, and refreshing in the background. Preserve every other app’s settings.',r,path)
 e.update(case=r['episode'],personaId=r['persona'],run=2,ticks=r['final_tick'],completed=bool(r['goal_ok']),outcome='Task completed' if r['goal_ok'] else 'Goal not satisfied',
 dialogue=[{'tick':c['t'],'speaker':'assistant' if c['who']=='assistant' else 'user','text':c['text']} for c in r['timeline'] if c['kind']=='say' and c.get('text')],
 actions=[{'start':a['t'],'end':a['t'],'text':a['text']} for a in r['timeline'] if a['kind'] in ['gesture','blocked']])
 e['events']=[{'label':'Choose the wrong location permission' if b['kind']=='wrong_value' else 'Disable tracking for every app',
 'kind':'error','tick':b['injected_at'],'end':b['detected_tick'],'detectedAt':b['detected_tick'],'detected':b['detected'],'prevented':b['prevented']} for b in r['beats'] if b.get('injected_at') is not None]
 # Populated by deterministic replay, not dialogue assertions.
 e['milestones']=[]
 e['quality']=quality(f'screensim/tmp/bench_v2/aq_v4five/{model}/{r["episode"]}__{r["persona"]}.json',e['dialogue'])
 e['detection']={'detected':sum(b['detected'] for b in r['beats'] if not b.get('skipped')),'triggered':r['n_fired']}
 return save(e),r

def settings(r):
 return [(i['sub'],i['family'],i['err'],{k:v for k,v in i.get('report_keys',{}).get('anchor_v5',{}).items() if k!='prep_live'}) for i in r['injections']]

def main():
 peer,c=cook('cooking-peer','gemini-3.8-flash','classic_expert','b3_hard_nops_medium_map_1')
 base=load('cook-bench-engine/tmp/formal_v5/frames/classic_expert/gpt-6-astra/b3_hard_nops_medium_map_1.json')
 assert settings(base)==settings(c)
 v,vr=vh();s,sr=screen()
 vb=load('vh-streaming-engine/tmp/bench_v1/gemini-3.8-flash/gemini-3.8-flash__cx_tidybedroom_stall_place__safety_stepper.json')
 assert vr['task']==vb['task'] and vr['persona']==vb['persona'] and vr['targets']==vb['targets']
 assert [p['err'] for p in vr['phases']]==[p['err'] for p in vb['phases']]
 sb=json.loads((ROOT/'.work/screensim-record.json').read_text())
 assert all(sr[k]==sb[k] for k in ['episode','task','persona','n_designed'])
 assert [b['kind'] for b in sr['beats']]==[b['kind'] for b in sb['beats']]
 ps=[];previous=None
 for p in ['classic_novice','baseline','classic_expert']:
  e,r=cook('persona-'+p,'gpt-6-astra',p,'b3_master_nops_hard_map_5');ps.append(e['id'])
  assert r['outcome']=='won'
  if previous is not None:assert settings(previous)==settings(r)
  previous=r
 manifest={'comparisons':[
 {'id':'cooking','engine':'CookSim','episodes':['cooking','cooking-peer'],'setting':'Same kitchen, recipe, persona, and state-triggered event schedule.'},
 {'id':'household','engine':'VHSim','episodes':['household','household-peer'],'setting':'Same apartment, task, persona, and scheduled pause and placement error.'},
 {'id':'mobile','engine':'ScreenSim','episodes':['mobile','mobile-peer'],'setting':'Same phone configuration, task, persona, and two scheduled setting errors.'}],
 'personas':{'episodes':ps,'model':'GPT-6 Astra','task':e['task'],'setting':'Same kitchen, recipe, assistant, and scheduled events; only the persona changes.'}}
 dump(SITE/'data/comparisons.json',manifest)
 print('Built matched comparisons and three-persona set. Shared CookSim task/event specifications verified.')

if __name__=='__main__':main()
