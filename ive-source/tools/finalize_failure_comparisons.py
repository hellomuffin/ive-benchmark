"""Attach exact terminal observations and readable, recipe-verified milestones."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'site';WS=ROOT.parent
for key in ['cooking-fire','cooking-wrong']:
    path=SITE/f'data/{key}.json';e=json.loads(path.read_text());r=json.loads((WS/e['source']).read_text())
    final=f'assets/media/{key}-hd/{e["ticks"]:04d}.jpg'
    assert (SITE/final).exists()
    e['finalObservation']={'path':final,'crops':{'main':[962,26,960,720],'context':[0,26,960,720]},'provenance':'Rendered from the terminal recorded world state.'}
    for event in e['events']:
        if event['label'] in ['error','add foreign']:
            original=next(i for i in r['injections'] if i.get('report_keys',{}).get('injected_at')==event['tick'])
            event['label']={'wrong_order':'Assemble ingredients out of order','mis_prep':'Prepare an ingredient incorrectly','wrong_ingredient':'Use the wrong ingredient','add_foreign':'Add an extra ingredient','leave_unattended':'Leave cooking unattended'}.get(original['err'],original['err'].replace('_',' '))
    required=[('tortilla','raw'),('rice','cooked'),('steak','cooked'),('tomato','chopped'),('lettuce','chopped')]
    final_build=max((p['build'] for p in r['plate_seq']),default=0)
    plated=[p for p in r['plate_seq'] if p['build']==final_build]
    e['milestones']=[]
    for index,(item,state) in enumerate(required):
        correct=len(plated)>index and all((p['item'],p['state'])==required[i] for i,p in enumerate(plated[:index+1]))
        e['milestones'].append({'label':f'{state.capitalize()} {item}','tick':plated[index]['t'] if correct else e['ticks']+1})
    e['milestones'].append({'label':'Correct serving','tick':e['ticks'] if e['completed'] else e['ticks']+1})
    path.write_text(json.dumps(e,ensure_ascii=False,indent=2)+'\n')
