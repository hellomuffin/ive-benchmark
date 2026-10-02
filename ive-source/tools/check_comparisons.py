"""Visual, playback, and source-integrity checks for recorded comparisons."""
import json,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'site';WS=ROOT.parent
BASE=(sys.argv[1] if len(sys.argv)>1 else 'http://localhost:8793').rstrip('/')+'/'
manifest=json.loads((SITE/'data/comparisons.json').read_text())
ids=list(dict.fromkeys([i for pair in manifest['comparisons'] for i in pair['episodes']]+manifest['personas']['episodes']+['failure-delay','failure-interrupt']))
for key in ids:
 e=json.loads((SITE/f'data/{key}.json').read_text())
 assert e['playback']['duration']>0
 for d in e['dialogue']:
  assert (SITE/d['audio']).is_file(),(key,d['audio'])
  assert 0<=d['start']<e['playback']['duration']
 if e.get('source'):
  path=WS/e['source']
  if path.suffix=='.json':
   r=json.loads(path.read_text());lines={(x['t'],'assistant' if x['speaker']=='vlm' else 'user',x.get('text','')) for x in r['conversation']}
  else:
   r=next(json.loads(l) for l in path.open() if json.loads(l).get('episode')==e['case'] and json.loads(l).get('persona')==e['personaId'])
   lines={(x['t'],'assistant' if x['who']=='assistant' else 'user',x.get('text','')) for x in r['timeline'] if x['kind']=='say'}
  assert all((d['tick'],d['speaker'],d['text']) in lines for d in e['dialogue']),key
print('Verbatim dialogue and audio assets verified for',len(ids),'recordings.')
with sync_playwright() as p:
 b=p.chromium.launch(args=['--no-sandbox']);page=b.new_page(viewport={'width':1440,'height':1100});errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.on('response',lambda r:errors.append(f'{r.status} {r.url}') if r.status>=400 and r.url.startswith(BASE) else None)
 page.add_init_script('window.audioStarted=0;const play=HTMLMediaElement.prototype.play;HTMLMediaElement.prototype.play=function(){const r=play.call(this);r?.then(()=>window.audioStarted++).catch(()=>{});return r;}')
 page.goto(BASE,wait_until='networkidle');page.wait_for_function('document.querySelectorAll(".recorded-replay").length===7')
 assert page.locator('.facts').count()==0
 for key in ['cooking','household','mobile']:
  page.locator(f'[data-episode="{key}"]').click();page.wait_for_timeout(800)
  assert page.locator('#matched-comparison .recorded-replay').count()==2
  pair=next(x for x in manifest['comparisons'] if x['id']==key)
  for i,episode_id in enumerate(pair['episodes']):
   e=json.loads((SITE/f'data/{episode_id}.json').read_text());card=page.locator('#matched-comparison .recorded-replay').nth(i)
   first=e['dialogue'][0]['start']
   card.locator('input').evaluate('(el,v)=>{el.value=v;el.dispatchEvent(new Event("input",{bubbles:true}));}',first+.05)
   card.locator('.replay-play').click();page.wait_for_timeout(600);card.locator('.replay-play').click()
   assert card.locator('.replay-message').count()>0
   assert e['dialogue'][0]['text'] in card.locator('.replay-chat').inner_text()
  page.locator('#matched-comparison').screenshot(path=str(ROOT/f'.work/matched-{key}.png'))
 assert page.evaluate('window.audioStarted')>=6
 for key,host,i,tick in [('failure-delay','#recorded-failures',0,376),('failure-interrupt','#recorded-failures',1,13)]:
  e=json.loads((SITE/f'data/{key}.json').read_text());seg=next(s for s in e['playback']['segments'] if s['tick']==tick)
  card=page.locator(f'{host} .recorded-replay').nth(i)
  card.locator('input').evaluate('(el,v)=>{el.value=v;el.dispatchEvent(new Event("input",{bubbles:true}));}',seg['start']+.1)
 page.locator('#recorded-failures').screenshot(path=str(ROOT/'.work/recorded-failures.png'))
 for i,key in enumerate(manifest['personas']['episodes']):
  e=json.loads((SITE/f'data/{key}.json').read_text());card=page.locator('#persona-replays .recorded-replay').nth(i)
  first=e['dialogue'][0]['start'];card.locator('input').evaluate('(el,v)=>{el.value=v;el.dispatchEvent(new Event("input",{bubbles:true}));}',first+.1)
 page.locator('#persona-replays').screenshot(path=str(ROOT/'.work/persona-comparison.png'))
 for width in [390,768,1440]:
  page.set_viewport_size({'width':width,'height':1050});page.wait_for_timeout(300)
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),f'Overflow at {width}'
  size=page.locator('.replay-message').first.evaluate('(e)=>parseFloat(getComputedStyle(e).fontSize)');assert size>=14
 page.set_viewport_size({'width':390,'height':844});page.locator('#experience').scroll_into_view_if_needed();page.screenshot(path=str(ROOT/'.work/comparison-mobile.png'))
 assert not errors,errors
 b.close()
print('All comparisons, speech playback, failure excerpts, persona cards, and responsive widths passed.')
