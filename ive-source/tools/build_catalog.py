"""Export exact case/persona membership, not runtime prompts or simulator assets."""
from pathlib import Path
import ast,hashlib,json
ROOT=Path(__file__).resolve().parents[1];WS=ROOT.parent
sources={
 'cooksim':'cook-bench-engine/tmp/interact_eval/cases_composite_v4.json',
 'vhhome':'vh-streaming-engine/docs/BENCH_V1_CELLS.json',
 'screensim':'screensim/docs/bench_persona_assignment.json'}
data={k:json.loads((WS/p).read_text()) for k,p in sources.items()}
engines={
 'cooksim':[{'case_id':c['name'],'persona_id':p} for c in data['cooksim']['cases'] for p in ['baseline','classic_novice','classic_expert']],
 'vhhome':[{'case_id':c['case'],'persona_id':c['persona']} for c in data['vhhome']['cells']],
 'screensim':[{'case_id':c,'persona_id':p} for c,ps in data['screensim']['assignment'].items() for p in ps]}
for e,n in [('cooksim',150),('vhhome',75),('screensim',90)]:
 assert len(engines[e])==n
 assert len({(x['case_id'],x['persona_id']) for x in engines[e]})==n
cook_observed={(p.stem,p.parents[1].name) for p in (WS/'cook-bench-engine/tmp/formal_v5/frames').glob('*/gpt-6-astra/b3_*.json')}
assert cook_observed=={(x['case_id'],x['persona_id']) for x in engines['cooksim']}
for cell in engines['vhhome']:
 assert (WS/f"vh-streaming-engine/tmp/bench_v1/gemini-3.8-flash/gemini-3.8-flash__{cell['case_id']}__{cell['persona_id']}.json").is_file()
screen_records=[json.loads(line) for line in (WS/'screensim/tmp/bench_v2/gemini-3.1-pro-preview.records.jsonl').open()]
assert {(x['case_id'],x['persona_id']) for x in engines['screensim']} <= {(r.get('episode'),r.get('persona')) for r in screen_records}
personas={}
tree=ast.parse((WS/'cook-bench-engine/cooksim/interact/persona_v2.py').read_text())
for node in tree.body:
 if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ROSTER' for t in node.targets):
  for call in node.value.elts:
   args=[ast.literal_eval(a) for a in call.args];name=next(ast.literal_eval(k.value) for k in call.keywords if k.arg=='name')
   personas[name]=dict(zip(['skill','trust','pace_level','alerting_level','interruption_level'],args))
out={'benchmark_version':'ive-v1','underlying_cases':105,'episodes_per_run':315,'independent_runs':3,
 'source_files':{k:{'path':p,'sha256':hashlib.sha256((WS/p).read_bytes()).hexdigest()} for k,p in sources.items()},
 'engines':engines,'personas':personas,
 'note':'Membership catalog for submission checks. This is not the executable task specification or a substitute for simulator packages.'}
path=ROOT/'site/data/benchmark-catalog.json';path.write_text(json.dumps(out,indent=2)+'\n')
print('Exported 105 cases and 315 exact case/persona pairs.')
