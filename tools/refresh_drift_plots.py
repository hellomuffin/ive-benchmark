"""Refresh the two rollout illustrations from the paper's fixed-timing runs."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from statistics import fmean
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT.parent
SOURCE=BASE/'cook-bench-engine/tmp/formal_v7_lat2'
CACHE=json.loads((BASE/'cook-bench-engine/tmp/formal_results_cache_v7c.json').read_text())
IDS={'truthful':['T1','T2'],'sensible':['S1','S2'],'helpful':['H1','H2','H3']}
LABELS=['Factual grounding','Situational relevance','Actionable guidance']
COLORS=['#407da5','#9c7eac','#bc7958']
out={'condition':'fixed','runs':[1,2,3],'judges':['gemini','gpt'],'models':{}}

def one(p):
    d=json.loads(p.read_text())
    raw=Path(str(p).replace('/sq_v4/','/'))
    assert raw.stat().st_mtime==CACHE[str(raw)]['mtime']
    ticks=CACHE[str(raw)]['rec']['ticks']; rows=[]
    for r in d['rounds']:
        if r.get('t') is None: continue
        index=min(9,max(0,int(10*r['t']/ticks)))
        vals={}
        for cat,ids in IDS.items():
            judges=[]
            for j in ['gemini','gpt']:
                items=(r.get('judges',{}).get(j) or {}).get('items') or {}
                ps=[items.get(i,{}).get('pass') for i in ids if items.get(i,{}).get('pass') is not None]
                if ps:judges.append(float(not any(x is False for x in ps)))
            if judges:vals[cat]=fmean(judges)
        rows.append((index,vals))
    return rows

for tag,title,slug in [('qwen3.8-27b','Qwen3.8-27B','qwen'),('museglimmer','Muse Glimmer','glimmer')]:
    runs=[]
    for run in [1,2,3]:
        arm=tag+('' if run==1 else f'__r{run}')
        files=list((SOURCE/'sq_v4/frames').glob(f'*/{arm}/b3_*.json'));assert len(files)==150
        bins={c:[[] for _ in range(10)] for c in IDS}
        with ThreadPoolExecutor(max_workers=8) as pool:
            for rows in pool.map(one,files):
                for i,vs in rows:
                    for c,v in vs.items():bins[c][i].append(v)
        runs.append({c:[fmean(b) if b else None for b in bins[c]] for c in IDS})
    curves={c:[100*fmean(r[c][i] for r in runs if r[c][i] is not None) for i in range(10)] for c in IDS}
    out['models'][tag]={'curves':curves,'run_curves':runs}
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,ax=plt.subplots(figsize=(5.8,3.25),layout='constrained')
    ax.set_title(title,loc='left',fontweight='bold',fontsize=13,pad=14,color='#274258')
    for (cat,vs),label,col in zip(curves.items(),LABELS,COLORS):ax.plot(range(5,100,10),vs,label=label,color=col,linewidth=2.2,marker='o',markersize=3.7)
    ax.set(xlim=(0,100),ylim=(0,100),xlabel='Episode progress (%)',ylabel='Category pass rate (%)')
    ax.set_xticks([0,25,50,75,100]);ax.set_yticks([0,25,50,75,100]);ax.grid(axis='y',color='#e8edf1');ax.set_axisbelow(True)
    for s in ['left','bottom']:ax.spines[s].set_color('#bacbd8')
    ax.tick_params(colors='#647b8b',length=3);ax.legend(loc='lower left',frameon=False,fontsize=8)
    fig.savefig(ROOT/f'docs/redesign/technical/media/drift-{slug}.png',dpi=180);plt.close(fig)
    print(title,'refreshed',flush=True)
(ROOT/'docs/redesign/technical/drift-results.json').write_text(json.dumps(out,indent=2)+'\n')
