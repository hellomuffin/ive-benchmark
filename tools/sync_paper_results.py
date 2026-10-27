"""Export the paper's audited three-run results without regrading or rounding.

Usage: python tools/sync_paper_results.py --paper ../arxiv-Interactive-Visual-Gym
"""
import argparse
import hashlib
import html
import json
from pathlib import Path
import re
from statistics import fmean
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--paper', type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
paper = args.paper.resolve()
snapshot = paper / 'tables/v7_results_snapshot.json'
data = json.loads(snapshot.read_text())
commit = subprocess.check_output(['git', '-C', str(paper), 'rev-parse', 'HEAD'], text=True).strip()
families = ['Frontier API', 'Streaming API', 'Open non-streaming', 'Open streaming']
engines = {'CookSim': 'cooksim', 'VHSim': 'vhhome', 'ScreenSim': 'screensim'}
rubrics = ['truthful', 'sensible', 'helpful', 'listens', 'economy']
output = {
    'version': 'IVG-Bench · arXiv paper results',
    'sourceCommit': commit,
    'sourceRepository': 'https://github.com/hellomuffin/-arxiv-Interactive-Visual-Gym',
    'sourceSnapshotSHA256': hashlib.sha256(snapshot.read_bytes()).hexdigest(),
    'defaultCondition': 'fixed',
    'conditions': {
        'fixed': {'label': 'Without measured delay', 'timing': {'cooksim': 'Fixed two-tick delivery', 'vhhome': 'Fixed two-tick delivery', 'screensim': 'Fixed zero-tick delivery'}},
        'measured': {'label': 'With measured delay', 'timing': {'cooksim': 'Measured assistant latency', 'vhhome': 'Measured assistant latency', 'screensim': 'Same action–response evaluation'}},
    },
    'aggregation': {'runs': 'Equal-weight mean of three independent runs', 'overall': 'Equal-weight mean across the three environments', 'judges': data['provenance']['judges'], 'quality': data['provenance']['quality']},
    'models': [],
}
for (family, tags), public_family in zip(data['families'], families):
    for tag in tags:
        model = {'id': tag, 'model': data['names'][tag], 'family': public_family, 'conditions': {}}
        for condition in output['conditions']:
            rows = {}
            for source, key in engines.items():
                row = data['conditions'][condition][source][tag]
                v = row['values']
                rows[key] = {
                    'success': 100*v[0], 'quality': 100*v[7], 'recall': 100*v[1],
                    'successSD': 100*row['run_sd'][0],
                    'rubrics': dict(zip(rubrics, [100*x for x in v[2:7]])),
                    'runs': [{'run': r['run'], 'episodes': r['n'], 'success': 100*r['success'], 'quality': 100*r['quality'], 'recall': 100*r['recall']} for r in row['runs']],
                }
            model['conditions'][condition] = {'engines': rows, 'overall': {metric: fmean(row[metric] for row in rows.values()) for metric in ['success', 'quality', 'recall']}}
        # The older landing page also consumes these fields; its default now
        # agrees with the paper instead of retaining the stale measured results.
        model.update(model['conditions']['fixed'])
        output['models'].append(model)
(root / 'docs/data/leaderboard.json').write_text(json.dumps(output, indent=2)+'\n')

# Copy the active abstract exactly; leave historical commented drafts alone.
tex = '\n'.join(line for line in (paper/'sections/abstract_body.tex').read_text().splitlines() if not line.lstrip().startswith('%')).strip()
abstract = html.escape(tex)
abstract = re.sub(r'\\textbf\{([^{}]+)\}', r'<strong>\1</strong>', abstract).replace(r'\%', '%')
abstract = re.sub(r'\s+', ' ', abstract)
page = root / 'docs/redesign/index.html'
text = page.read_text()
text, count = re.subn(r'(<p class="abstract-copy">).*?(</p>)', lambda m: m[1]+abstract+m[2], text, count=1, flags=re.S)
assert count == 1
text = text.replace('Evaluating visual assistants with simulated human users in interactive worlds', 'Evaluating visual interaction models with simulated human users in interactive worlds')
page.write_text(text)
print(f'Exported {len(output["models"])} models × 2 timing conditions from {commit[:12]}')
