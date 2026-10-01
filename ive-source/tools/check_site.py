from pathlib import Path
import sys
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.work';OUT.mkdir(exist_ok=True)
BASE=(sys.argv[1] if len(sys.argv)>1 else 'http://localhost:8793').rstrip('/')+'/'
with sync_playwright() as p:
 browser=p.chromium.launch(args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1)
 page.add_init_script("""window.__audioStarts=0;const original=HTMLMediaElement.prototype.play;
 HTMLMediaElement.prototype.play=function(...args){const result=original.apply(this,args);
 if(result)result.then(()=>window.__audioStarts++).catch(()=>{});return result};""")
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.on('response',lambda r:errors.append(f'HTTP {r.status}: {r.url}') if r.status>=400 and r.url.startswith(BASE) else None)
 page.goto(BASE,wait_until='networkidle')
 page.screenshot(path=str(OUT/'desktop.png'),full_page=True)
 page.locator('[data-jump="56"]').click()
 page.wait_for_timeout(1400)
 assert page.evaluate('window.__audioStarts>0'),'Narration never began playing'
 page.locator('#play').click()
 page.locator('#episode').screenshot(path=str(OUT/'player.png'))
 page.locator('[data-view="map"]').click()
 page.locator('#scene').screenshot(path=str(OUT/'enlarged-map.png'))
 page.locator('[data-view="combined"]').click()
 page.locator('#watch-film').click()
 page.wait_for_function('document.querySelector("#film").currentTime > 0')
 page.locator('#close-film').click()
 assert page.locator('#film').evaluate('(v)=>v.paused')
 assert page.locator('#leaderboard-table tbody tr').count()==14
 page.locator('[data-engine="cooksim"]').click()
 page.locator('#model-search').fill('Astra')
 assert page.locator('#leaderboard-table tbody tr').count()==1
 page.locator('#model-search').fill('')
 page.locator('#scatter').screenshot(path=str(OUT/'plot.png'))
 for key in ['household','mobile']:
  page.locator(f'[data-episode="{key}"]').click()
  page.wait_for_timeout(500)
  page.locator('#events button').first.click()
  page.wait_for_timeout(300)
  page.locator('#episode').screenshot(path=str(OUT/f'{key}-player.png'))
  assert page.locator('#clock').inner_text()!='TICK 000'
  for selector in ['#video-link','#captions-link']:
   response=page.request.get(BASE+page.locator(selector).get_attribute('href'))
   assert response.ok,selector
 print('Loaded fonts:',page.evaluate('Array.from(document.fonts).map(f=>({family:f.family,status:f.status}))'))
 page.locator('#submission-file').set_input_files(str(ROOT/'site/submission/example.json'))
 page.wait_for_function('document.querySelector("#validation-result").textContent.includes("Valid single-episode")')
 page.locator('#submission-file').set_input_files({'name':'invalid.json','mimeType':'application/json','buffer':b'[]'})
 page.wait_for_function('document.querySelector("#validation-result").textContent.includes("JSON object")')
 result=page.evaluate('''async()=>{const {validateManifest}=await import('./submission.js');const c=await fetch('data/benchmark-catalog.json').then(r=>r.json());
 const d={benchmark_version:'ive-v1',model:{name:'Test only',revision:'test',family:'Frontier API'},runs:[]};
 for(const [engine,cells] of Object.entries(c.engines))for(const run_id of [1,2,3])d.runs.push({engine,run_id,episodes:cells.map(x=>({...x,trace_uri:'test.json',trace_sha256:'0'.repeat(64)}))});
 return validateManifest(d,c,true)}''')
 assert result==[],result
 page.goto(BASE+'?episode=mobile&tick=9#experience',wait_until='networkidle')
 assert page.locator('#clock').inner_text()=='TICK 009'
 assert page.locator('#assistant').inner_text()=='Gemini 3.1 Pro'
 page.set_viewport_size({'width':390,'height':844})
 page.goto(BASE,wait_until='networkidle')
 page.screenshot(path=str(OUT/'mobile.png'),full_page=True)
 assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Horizontal overflow'
 for width in [390,768,1440]:
  page.set_viewport_size({'width':width,'height':1000})
  page.goto(BASE+'?episode=cooking&tick=56#experience',wait_until='networkidle')
  for selector in ['.milestone','.event-chip b','.message']:
   size=page.locator(selector).first.evaluate('(e)=>parseFloat(getComputedStyle(e).fontSize)')
   assert size>=15,(selector,width,size)
  assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),width
 page.locator('.state-grid').screenshot(path=str(OUT/'research-status.png'))
 page.goto(BASE+'submission.html',wait_until='networkidle')
 page.wait_for_function('document.querySelector("#manifest-example").textContent.includes("benchmark_version")')
 assert page.locator('h1').inner_text()=='Submission guide'
 page.locator('#submission-file').set_input_files(str(ROOT/'site/submission/example.json'))
 page.wait_for_function('document.querySelector("#validation-result").textContent.includes("Valid single-episode")')
 page.screenshot(path=str(OUT/'submission-guide.png'),full_page=True)
 page.set_viewport_size({'width':390,'height':844})
 page.goto(BASE+'submission.html',wait_until='networkidle')
 assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),'Guide overflow'
 page.screenshot(path=str(OUT/'submission-guide-mobile.png'),full_page=True)
 browser.close()
 print('Browser errors:',errors)
 assert not errors
