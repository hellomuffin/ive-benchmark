"""Check every published score against the paper, not rounded table strings."""
from pathlib import Path
from statistics import fmean
import json
import math
import html
import re
import hashlib

ROOT=Path(__file__).resolve().parents[1]
PAPER=ROOT.parent/'arxiv-Interactive-Visual-Gym'
snapshot=PAPER/'tables/v7_results_snapshot.json'
paper=json.loads(snapshot.read_text())
site=json.loads((ROOT/'docs/data/leaderboard.json').read_text())
display=json.loads((PAPER/'tables/results_display.json').read_text())
assert {m['id'] for m in site['models']}==set(display['main_models'])
assert len(site['models'])==15
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
tex=' '.join(line for line in (PAPER/'sections/abstract_body.tex').read_text().splitlines() if not line.lstrip().startswith('%'))
tex=re.sub(r'\\textbf\{([^{}]+)\}',r'\1',tex).replace(r'\%', '%')
web=re.search(r'<p class="abstract-copy">(.*?)</p>',page,re.S).group(1)
web=html.unescape(re.sub(r'<[^>]+>','',web))
assert ' '.join(tex.split())==' '.join(web.split()), 'Website abstract differs from the active paper abstract'
assert site['sourceSnapshotSHA256']==hashlib.sha256(snapshot.read_bytes()).hexdigest()
best=max(site['models'],key=lambda m:m['conditions']['fixed']['overall']['success'])
headline=f"{best['conditions']['fixed']['overall']['success']:.1f}"
for filename in ['abstract_body.tex','intro.tex','quantitative_v7.tex']:
    text='\n'.join(line for line in (PAPER/'sections'/filename).read_text().splitlines() if not line.lstrip().startswith('%'))
    assert best['model'] in text and headline+r'\%' in text,filename
assert 'visual interaction models' in page
print(f'PASS: {checks} scores match the paper; three-run means and both cross-environment views verified; exact abstract and headline agreement verified.')
