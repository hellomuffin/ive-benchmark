"""Build the public release from pinned, local benchmark artifacts.

Only explicitly selected fields are exported. Original prompts, credentials,
participant data, and machine-specific absolute paths never enter the site.
"""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
PUBLIC = ROOT / 'site'
PAPER = WORKSPACE / '.release-work/paper-latest'
CATEGORIES = {'truthful': ['T1','T2'], 'sensible': ['S1','S2'],
              'helpful': ['H1','H2','H3'], 'listens': ['L1','L2'], 'economy': ['E1']}
NAMES = ['Factual grounding','Situational relevance','Actionable guidance','User intent uptake','Guidance conciseness']
FAMILIES = [
 ('Frontier API', ['GPT-6 Astra','Gemini 3.1 Pro','Gemini 3.8 Flash']),
 ('Streaming API', ['Gemini 3.8 Live','GPT-Realtime 2.1']),
 ('Open non-streaming', ['Qwen3.8-27B','Molmo2-8B','InternVideo3-8B','Kimi-VL-A3B-Thinking','Muse Glimmer']),
 ('Open streaming', ['MiniCPM-o 4.5','Qwen3-Omni-30B','Proact-VL','StreamingVLM'])]
COOK = 'cook-bench-engine/tmp/formal_v5/frames/classic_expert/gpt-6-astra/b3_hard_nops_medium_map_1.json'
VH = 'vh-streaming-engine/tmp/bench_v1/gemini-3.8-flash/gemini-3.8-flash__cx_tidybedroom_stall_place__safety_stepper.json'
SCREEN_CASE = 'app_privacy_quarantine__c2'

def read(p): return json.loads((WORKSPACE / p).read_text())
def dump(p,x):
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def quality(path, dialogue):
 d=read(path); out=[]
 rounds=d.get('rounds_detail',d.get('rounds',[]))
 for i,r in enumerate(rounds):
  groups=[v['items'] for v in (r.get('judges') or {}).values() if isinstance(v,dict) and v.get('items')]
  if not groups:groups=[r.get('items') or {}]
  if not any(groups):continue
  items=groups[0]
  flags={};gates=[]
  for c,ids in CATEGORIES.items():
   clean=[]
   for its in groups:
    vals=[its[k]['pass'] for k in ids if k in its and its[k].get('pass') is not None]
    if vals:clean.append(int(all(vals)))
   flags[c]=sum(clean)/len(clean) if clean else None
  applicable=[v for v in flags.values() if v is not None]
  if not applicable:continue
  # Match sq_v4_three_runs.py: average judge gates and clean category scores,
  # then multiply the gate by the mean of applicable categories.
  gates=[int(not any((its.get(k) or {}).get('pass') is False for k in ['T1','T2'])) for its in groups]
  score=(sum(gates)/len(gates))*sum(applicable)/len(applicable)
  t=r.get('t',r.get('tick'))
  if t is None:
   assistants=[v for v in dialogue if v['speaker']=='assistant']
   t=assistants[i]['tick'] if i<len(assistants) else 0
  out.append({'tick':t,'score':score,'categories':flags,'evidence':[
   {'id':k,'judgeIndex':j,'pass':v.get('pass'),'reason':v.get('reason','')}
   for j,its in enumerate(groups) for k,v in its.items() if any(k in ids for ids in CATEGORIES.values())]})
 means={c:sum(v[c] for v in [x['categories'] for x in out] if v[c] is not None)/max(1,sum(x['categories'][c] is not None for x in out)) for c in CATEGORIES}
 return {'overall':sum(x['score'] for x in out)/len(out) if out else None,'categories':means,'rounds':out,'source':path,'judge':d.get('judge',d.get('judges'))}

def common(key,engine,model,persona,axes,task,record,source):
 return {'id':key,'engine':engine,'model':model,'persona':persona,'axes':axes,'task':task,
   'source':source,'sourceHash':digest(WORKSPACE/source),'engineVersion':record.get('engine_rev'),
   'media':f'assets/media/{key}.mp4','poster':f'assets/media/{key}.jpg',
   'timingNote':'Recorded text interaction. Synthetic voices added for presentation; playback is time-expanded. Tick stamps preserve the original sequence.'}

def cook():
 r=read(COOK); e=common('cooking','CookSim','GPT-6 Astra','Independent expert',[3,1,2,1,3],
  'Cook and serve a Fish & Chips Platter: cooked fish followed by two portions of cooked potato.',r,COOK)
 e['dialogue']=[{'tick':c['t'],'speaker':'assistant' if c['speaker']=='vlm' else 'user','text':c['text']} for c in r['conversation'] if c.get('text','').strip()]
 e['actions']=[{'start':a['t_issue'],'end':a.get('t_done') or a['t_issue'],'text':a['cmd']} for a in r['actions']]
 e['events']=[]
 labels={'serve_raw':'Plate raw fish','forget_next_step':'Forget to turn on the heat','repeat_step':'Repeat an ingredient step'}
 for inj in r['injections']:
  k=inj.get('report_keys',{}); t=k.get('injected_at'); fam=inj['family']
  if t is None:continue
  label=labels.get(inj.get('err'),{'qa_probe':'Ask a temporal question','qa_proactive':'Request a readiness alert','plan_change':'Add fresh lettuce'}.get(fam,fam))
  if fam=='qa_probe':label='Recall earlier fryer advice' if t==98 else 'Ask about cooking status'
  e['events'].append({'label':label,'kind':fam,'tick':t,'detectedAt':inj.get('detected_at') or inj.get('cook_detected_at'),
   'end':k.get('released_at',inj.get('archived_at',t)), 'commit':k.get('committed_at'),
   'detected':bool(inj.get('flagged_valid')),'prevented':bool(inj.get('prevented')),
   'detail':(inj.get('qa') or {}).get('question_as_asked',''),
   'answeredAt':(inj.get('qa') or {}).get('answered_at'),
   'alertAt':(inj.get('proactive') or {}).get('alert_t'),
   'result':(inj.get('proactive') or {}).get('verdict')})
 # Milestones are derived from recorded physical state changes, not assistant estimates.
 e['milestones']=[{'label':'Prepare fish','tick':r['prepped']['fish']}, {'label':'Cook fish','tick':r['heat_events'][0]['cooked_at']},
  {'label':'First potato cooked','tick':r['heat_events'][1]['cooked_at']}, {'label':'Complete plate','tick':197},
  {'label':'Serve','tick':r['ticks']}]
 e['goalChanges']=[{'tick':193,'text':'User adds fresh lettuce to the recipe.'}]
 e['ticks']=r['ticks'];e['outcome']='Task completed';e['rawVideo']=COOK.replace('.json','.mp4');e['rawTicksPerSecond']=6
 e['crops']={'main':[522,26,520,370],'context':[0,26,520,370]}
 e['quality']=quality(COOK.replace('/frames/','/sq_v4/frames/'),e['dialogue'])
 e['detection']={'detected':sum(x['detected'] for x in e['events'] if x['kind']=='error'),'triggered':sum(x['kind']=='error' for x in e['events'])}
 e['caption']='The assistant catches mistakes, responds to a readiness request, and negotiates a recipe change.'
 e['chapters']=[{'tick':13,'label':'Raw ingredient'}, {'tick':38,'label':'Recovery'}, {'tick':113,'label':'Proactive request'}, {'tick':193,'label':'Plan change'}]
 return e

def vh():
 r=read(VH);e=common('household','VHSim','Gemini 3.8 Flash','Cautious collaborator',[2,3,1,3,1],
  'Tidy the bedroom: return the book to the desk, close the cabinet, turn off the lamp, and bring the mug to the kitchen table.',r,VH)
 e['dialogue']=[{'tick':c['t'],'speaker':'assistant' if c['speaker']=='vlm' else 'user','text':c['text']} for c in r['conversation'] if c.get('text','').strip()]
 e['actions']=[{'start':a['t_issue'],'end':a.get('t_done') or a['t_issue'],'text':a['cmd']} for a in r['action_log']]
 e['events']=[{'label':'Pause while holding the book' if p['err']=='stall' else 'Put the mug on the wrong surface','kind':'error',
   'tick':p['injected_at'],'end':p['released_at'],'commit':p['released_at'] if not p.get('prevented') else None,
   'detectedAt':next((f['t'] for f in p.get('flags',[]) if f.get('verdict')=='valid'),None),
   'detected':p.get('caught',False),'prevented':p.get('prevented',False)} for p in r['phases']]
 e['milestones']=[{'label':'Book on desk','tick':65},{'label':'Cabinet closed','tick':74},{'label':'Lamp off','tick':82},{'label':'Mug on table','tick':120}]
 e['ticks']=r['ticks'];e['outcome']='Task completed';e['rawVideo']=VH.replace('.json','.mp4');e['rawTicksPerSecond']=1
 e['crops']={'main':[0,24,640,456],'context':[640,24,480,456]}
 e['quality']=quality(VH.replace('/gemini-3.8-flash/','/sq_v4/gemini-3.8-flash/'),e['dialogue'])
 e['detection']={'detected':sum(x['detected'] for x in e['events']),'triggered':len(e['events'])}
 e['caption']='A misplaced mug leads to a correction and a visible change in the user’s next actions.'
 e['chapters']=[{'tick':45,'label':'Scheduled pause'},{'tick':65,'label':'Task progress'},{'tick':90,'label':'Wrong placement'},{'tick':104,'label':'Correction'}]
 return e

def screen():
 p=next(x for x in read('screensim/tmp/showcase/picks.json') if x['episode']==SCREEN_CASE)
 source='screensim/'+p['source']
 r=next(x for x in (json.loads(l) for l in (WORKSPACE/source).open()) if x.get('episode')==SCREEN_CASE and x.get('persona')==p['persona'] and x.get('contestant')==p['seat'])
 dump(ROOT/'.work/screensim-record.json',r)
 e=common('mobile','ScreenSim','Gemini 3.1 Pro','Hurried, skeptical user',[2,1,3,2,3],
  'Stop TripSnap from accessing location, tracking activity, and refreshing in the background. Preserve every other app’s settings.',r,source)
 e['dialogue']=[{'tick':c['t'],'speaker':'assistant' if c['who']=='assistant' else 'user','text':c['text']} for c in r['timeline'] if c['kind']=='say' and c.get('text')]
 e['actions']=[{'start':a['t'],'end':a['t'],'text':a['text']} for a in r['timeline'] if a['kind'] in ['gesture','blocked']]
 e['events']=[{'label':'Choose the wrong location permission' if b['kind']=='wrong_value' else 'Disable tracking for every app','kind':'error',
  'tick':b['injected_at'],'end':b['detected_tick'],'detectedAt':b['detected_tick'],'detected':b['detected'],'prevented':b['prevented'],
  'detail':'ScreenSim credits correction within its error window; the mistaken setting is visible before correction.'} for b in r['beats']]
 e['milestones']=[{'label':'Location: Never','tick':10},{'label':'Background refresh off','tick':12},{'label':'Tracking off','tick':19}]
 e['ticks']=r['final_tick'];e['outcome']='Task completed';e['quality']=quality('screensim/'+p['grading'],e['dialogue'])
 e['detection']={'detected':r['n_fired'] if r['recall']==1 else round(r['recall']*r['n_fired']),'triggered':r['n_fired']}
 e['caption']='Two incorrect settings are caught while preserving the user’s “this app only” constraint.'
 e['chapters']=[{'tick':8,'label':'App permissions'},{'tick':9,'label':'Wrong value'},{'tick':17,'label':'Wrong target'},{'tick':19,'label':'Goal satisfied'}]
 return e

def leaderboard():
 snap=json.loads((PAPER/'tables/results_snapshot.json').read_text());rec=json.loads((PAPER/'tables/recall_snapshot.json').read_text())
 out=[]
 for family,names in FAMILIES:
  for name in names:
   engines={}
   for eng in ['cooksim','vhhome','screensim']:
    x=snap[eng]['models'][snap[eng]['display_mapping'][name]];rr=rec['engines'][eng]['models'][name]
    engines[eng]={'success':x['success']*100,'successSD':x.get('success_sd',0)*100,
     'quality':x['quality']['overall']*100,'recall':rr['recall']*100,
     'rubrics':{c:x['quality'][c]*100 for c in CATEGORIES},'detectionCounts':{'detected':rr.get('tp'),'triggered':rr.get('fired')},
     'runs':[{'run':v['run'],'episodes':v['n'],'success':v['success']*100} for v in x.get('runs',[])]}
   overall={k:sum(e[k] for e in engines.values())/3 for k in ['success','quality','recall']}
   overall['rubrics']={c:sum(e['rubrics'][c] for e in engines.values())/3 for c in CATEGORIES}
   out.append({'model':name,'family':family,'engines':engines,'overall':overall,'date':'2026-09-26','status':'Paper baseline'})
 return {'version':'IVE v1 · paper snapshot','sourceCommit':'69f62e53e294cb56dfb48eaa2ae542c2cbac0070','models':out,
  'aggregation':'Overall averages the three environments equally. Success and quality use three-run summaries; detection recall uses run 1.',
  'categories':dict(zip(CATEGORIES,NAMES)),'families':[x[0] for x in FAMILIES]}

def main():
 PUBLIC.mkdir(parents=True,exist_ok=True)
 eps=[cook(),vh(),screen()]
 for e in eps:
  e['events'].sort(key=lambda x:x['tick'])
  old=PUBLIC/f'data/{e["id"]}.json'
  if old.exists():
   previous=json.loads(old.read_text())
   if previous.get('sourceHash')==e['sourceHash']:
    for key in ['playback','frameCount']:
     if key in previous:e[key]=previous[key]
    lookup={(d['tick'],d['speaker'],d['text']):d for d in previous['dialogue']}
    for d in e['dialogue']:
     match=lookup.get((d['tick'],d['speaker'],d['text']),{})
     for key in ['audio','duration','start']:
      if key in match:d[key]=match[key]
 dump(ROOT/'.work/episodes-source.json',eps)
 for e in eps:
  public={k:v for k,v in e.items() if k not in ['rawVideo','rawTicksPerSecond']}
  dump(PUBLIC/f'data/{e["id"]}.json',public)
 dump(PUBLIC/'data/leaderboard.json',leaderboard())
 print('Built three episodes and 14 model rows from the pinned paper snapshot.')

if __name__=='__main__':main()
