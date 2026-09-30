from pathlib import Path
import sys
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.work';OUT.mkdir(exist_ok=True)
BASE=(sys.argv[1] if len(sys.argv)>1 else 'http://localhost:8793').rstrip('/')+'/'
with sync_playwright() as p:
 browser=p.chromium.launch(args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1)
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.on('response',lambda r:errors.append(f'HTTP {r.status}: {r.url}') if r.status>=400 and r.url.startswith(BASE) else None)
 page.goto(BASE,wait_until='networkidle')
 page.screenshot(path=str(OUT/'desktop.png'),full_page=True)
 page.locator('[data-jump="56"]').click()
 page.wait_for_timeout(1400)
 page.locator('#play').click()
 page.locator('#episode').screenshot(path=str(OUT/'player.png'))
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
 page.set_viewport_size({'width':390,'height':844})
 page.goto(BASE,wait_until='networkidle')
 page.screenshot(path=str(OUT/'mobile.png'),full_page=True)
 assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Horizontal overflow'
 browser.close()
 print('Browser errors:',errors)
 assert not errors
