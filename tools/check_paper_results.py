"""Check every published score against the paper, not rounded table strings."""
from pathlib import Path
from statistics import fmean
import json
import math

ROOT=Path(__file__).resolve().parents[1]
paper=json.loads((ROOT.parent/'arxiv-Interactive-Visual-Gym/tables/v7_results_snapshot.json').read_text())
site=json.loads((ROOT/'docs/data/leaderboard.json').read_text())
assert len(site['models'])==14
checks=0
for m in site['models']:
    for cond in ['fixed','measured']:
        for engine,key in [('CookSim','cooksim'),('VHSim','vhhome'),('ScreenSim','screensim')]:
            a=paper['conditions'][cond][engine][m['id']];b=m['conditions'][cond]['engines'][key]
            values=[b['success'],b['recall'],*b['rubrics'].values(),b['quality']]
            for x,y in zip(values,a['values']):assert math.isclose(x,100*y,abs_tol=1e-10);checks+=1
            assert len(b['runs'])==3
            for k in ['success','recall','quality']:assert math.isclose(b[k],fmean(r[k] for r in b['runs']),abs_tol=1e-10)
        for k in ['success','quality','recall']:assert math.isclose(m['conditions'][cond]['overall'][k],fmean(e[k] for e in m['conditions'][cond]['engines'].values()),abs_tol=1e-10)
    assert m['engines']==m['conditions']['fixed']['engines']
    assert m['conditions']['fixed']['engines']['screensim']==m['conditions']['measured']['engines']['screensim']
page=(ROOT/'docs/redesign/index.html').read_text()
assert '49.7%' in page and '44.2%' not in page
assert 'visual interaction models' in page
print(f'PASS: {checks} scores match the paper; three-run means and both cross-environment views verified.')
