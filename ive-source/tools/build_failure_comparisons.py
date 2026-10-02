"""Outcome-diverse, matched comparisons drawn from the recorded benchmark."""
import json
from build_comparison_data import cook, save, common, quality, conversation, MODELS, settings, WS, ROOT, SITE, dump

def household(key, model):
    case='cx_guest_skip_stall'; persona='baseline'
    path=f'vh-streaming-engine/tmp/bench_v1/{model}/{model}__{case}__{persona}.json'
    r=json.loads((WS/path).read_text())
    e=common(key,'VHSim',MODELS[model],'Balanced user',[2,2,2,2,2],
      'Prepare for a guest: load the plate and mug into the dishwasher, return the pillow to the bed, and switch off the TV.',r,path)
    e.update(case=case,personaId=persona,run=1,ticks=r['ticks'],completed=r['outcome']=='won',outcome=r['outcome'],
      dialogue=conversation(r),actions=[{'start':a['t_issue'],'end':a.get('t_done') or a['t_issue'],'text':a['cmd']} for a in r['action_log']],
      crops={'main':[0,24,640,456],'context':[640,24,480,456]})
    goals=[('plate','dishwasher','Plate in dishwasher'),('mug','dishwasher','Mug in dishwasher'),('pillow','bed','Pillow on bed')]
    e['milestones']=[]
    for obj,place,label in goals:
        matches=[a for a in r['action_log'] if a['status']=='done' and a['cmd'].startswith('put ') and obj in a['cmd'] and place in a['cmd']]
        e['milestones'].append({'label':label,'tick':matches[-1]['t_done'] if matches else r['ticks']+1})
    matches=[a for a in r['action_log'] if a['status']=='done' and a['cmd'].startswith('switch off') and 'tv' in a['cmd']]
    e['milestones'].append({'label':'TV off','tick':matches[-1]['t_done'] if matches else r['ticks']+1})
    e['events']=[{'label':{'skipped_step':'Skip a task step','stall':'Pause task execution'}.get(p['err'],p['err']),
      'kind':'error','tick':p['injected_at'],'end':p['released_at'],'detected':p.get('caught',False),
      'detectedAt':next((f['t'] for f in p.get('flags',[]) if f.get('verdict')=='valid'),None)} for p in r['phases'] if p.get('injected_at') is not None]
    e['quality']=quality(path.replace(f'/{model}/',f'/sq_v4/{model}/'),e['dialogue'])
    return save(e),r

def phone(key,model):
    path=f'screensim/tmp/bench_v2/{model}.records.jsonl';case='app_privacy_quarantine__c1';persona='baseline'
    r=next(r for r in map(json.loads,(WS/path).open()) if r['episode']==case and r['persona']==persona)
    dump(ROOT/f'.work/{key}-record.json',r)
    e=common(key,'ScreenSim',MODELS[model],'Balanced user',[2,2,2,2,2],
      'Stop TripSnap from accessing location, tracking activity, and refreshing in the background. Preserve other settings.',r,path)
    e.update(case=case,personaId=persona,run=2,ticks=r['final_tick'],completed=bool(r['goal_ok']),outcome='won' if r['goal_ok'] else 'goal_not_satisfied',
      dialogue=[{'tick':c['t'],'speaker':'assistant' if c['who']=='assistant' else 'user','text':c['text']} for c in r['timeline'] if c['kind']=='say' and c.get('text')],
      actions=[{'start':a['t'],'end':a['t'],'text':a['text']} for a in r['timeline'] if a['kind'] in ['gesture','blocked']])
    e['events']=[{'label':{'wrong_page':'Open the wrong settings page','wrong_value':'Choose the wrong permission'}.get(b['kind'],b['kind']),
      'kind':'error','tick':b['injected_at'],'end':b['detected_tick'],'detectedAt':b['detected_tick'],'detected':b['detected'],'prevented':b['prevented']} for b in r['beats'] if b.get('injected_at') is not None]
    e['milestones']=[]
    e['quality']=quality(f'screensim/tmp/bench_v2/aq_v4five/{model}/{case}__{persona}.json',e['dialogue'])
    return save(e),r

def main():
    a,ar=cook('cooking-fire','gpt-6-astra','classic_expert','b3_master_nops_hard_map_4')
    b,br=cook('cooking-wrong','gemini-3.8-flash','classic_expert','b3_master_nops_hard_map_4')
    assert settings(ar)==settings(br) and ar['outcome']=='burned' and br['outcome']=='wrong_serve'
    a,ar=household('household-timeout','gemini-3.8-flash')
    b,br=household('household-stalled','gemini-3.1-pro-preview')
    assert ar['task']==br['task'] and ar['persona']==br['persona'] and [p['err'] for p in ar['phases']]==[p['err'] for p in br['phases']]
    a,ar=phone('mobile-success','gpt-6-astra');b,br=phone('mobile-failure','gemini-3.8-flash')
    assert ar['beats_design']==br['beats_design'] and ar['goal_ok'] and not br['goal_ok']
    print('Verified matched settings for all three outcome-diverse comparisons.')

if __name__=='__main__':main()
