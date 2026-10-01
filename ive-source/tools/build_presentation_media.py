"""Presentation-only media from recorded states; never changes evaluation inputs."""
from pathlib import Path
import argparse,base64,copy,hashlib,io,json,sys,threading,time
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1];WS=ROOT.parent;SITE=ROOT/'site'

def cook():
 from playwright.sync_api import sync_playwright
 web=WS/'cook-bench-engine/web'
 class Handler(SimpleHTTPRequestHandler):
  def __init__(self,*a,**kw):super().__init__(*a,directory=str(web),**kw)
  def do_GET(self):
   if self.path.startswith('/static/'):self.path=self.path[7:]
   super().do_GET()
  def log_message(self,*a):pass
 server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
 threading.Thread(target=server.serve_forever,daemon=True).start()
 record=SITE/'data/cooking.json';e=json.loads(record.read_text())
 states_path=(WS/e['source']).with_suffix('.states.jsonl')
 states=[json.loads(l) for l in states_path.read_text().splitlines() if l.strip()]
 dest=SITE/'assets/media/cooking-hd';dest.mkdir(exist_ok=True)
 w,h=960,720
 with sync_playwright() as p:
  b=p.chromium.launch(args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  page=b.new_page(viewport={'width':w,'height':h})
  page.goto(f'http://127.0.0.1:{server.server_port}/headless_render.html?w={w}&h={h}',wait_until='load',timeout=180000)
  page.wait_for_function('()=>window.__renderFrameSbs !== undefined',timeout=90000)
  page.evaluate('(s)=>window.__renderFrame(s)',states[0])
  page.wait_for_function('()=>window.__envReady === true && (window.__loadsPending || 0) === 0',timeout=180000)
  for i,st in enumerate(states):
   path=dest/f'{i:04d}.jpg'
   if path.exists():
    if path.stat().st_size>250000:
     with Image.open(path) as image:image.convert('RGB').save(path,quality=88,optimize=True)
    continue
   start=time.monotonic()
   url=page.evaluate('(s)=>window.__renderFrameSbs(s,0.95)',st)
   with Image.open(io.BytesIO(base64.b64decode(url.split(',',1)[1]))) as image:
    image.convert('RGB').save(path,quality=88,optimize=True)
   if i%10==0:print(f'CookSim HD {i+1}/{len(states)} ({time.monotonic()-start:.1f}s/frame)',flush=True)
  b.close()
 server.shutdown()
 assert len(list(dest.glob('*.jpg')))==len(states)
 e['presentation']={'frameRoot':'assets/media/cooking-hd','frameCount':len(states),
  'crops':{'main':[w+2,26,w,h],'context':[0,26,w,h]},
  'description':'CookSim views re-rendered at 960 × 720 per view from the recorded world states. Evaluation observations are unchanged.',
  'stateSha256':hashlib.sha256(states_path.read_bytes()).hexdigest()}
 record.write_text(json.dumps(e,ensure_ascii=False))
 print('CookSim HD complete',flush=True)

def mobile():
 sys.path.insert(0,str(WS/'screensim'))
 import tools.film_hand as fh
 from screensim.core.engine import Device
 from screensim.tasks import by_id,resolve_dynamic
 from screensim.render.capture import Capturer
 record=json.loads((ROOT/'.work/screensim-record.json').read_text())
 task=by_id(record['task']);dev=Device(task.seed)
 if task.start_app!='home':dev.open_app(task.start_app)
 dest=SITE/'assets/media/mobile-gestures';dest.mkdir(exist_ok=True)
 class GestureFilm(fh.Film):
  def __init__(self,cap):
   self.cap=cap;self.hand=fh.Hand();self.hx=fh.SCREEN_W*.72;self.hy=fh.SCREEN_H*.86
   self.lift=1.;self.poster=None;self.n=0;self.tick=0;self.files=[]
  def frame(self,phone=None,hand=None,ripple=None,highlight=None,reps=1):
   phone=phone if phone is not None else self.phone
   stage=Image.new('RGB',(fh.SCREEN_W+80,fh.SCREEN_H+48),'#f4f6fa')
   ph=phone.copy()
   if highlight is not None:ImageDraw.Draw(ph,'RGBA').rectangle((highlight.x,highlight.y,highlight.x2,highlight.y2),fill=(0,0,0,22))
   stage.paste(ph,(fh.PHONE_X,fh.PHONE_Y),fh._screen_mask())
   if ripple:
    (x,y),r,col=ripple
    ImageDraw.Draw(stage,'RGBA').ellipse((fh.PHONE_X+x-r,fh.PHONE_Y+y-r,fh.PHONE_X+x+r,fh.PHONE_Y+y+r),outline=col,width=3)
   self.hand.draw(stage,*(hand if hand is not None else (self.hx,self.hy,0.,self.lift)))
   for _ in range(reps):
    path=dest/f'{self.tick:04d}-{len(self.files):03d}.jpg';stage.save(path,quality=86,optimize=True)
    self.files.append(str(path.relative_to(SITE)));self.n+=1
   return stage
 gestures={}
 with Capturer() as cap:
  film=GestureFilm(cap)
  for row in record['timeline']:
   kind=row['kind']
   if kind not in ['gesture','blocked']:continue
   pre=copy.deepcopy(dev);geo=fh.geometry(pre,resolve_dynamic(pre,row['text']))
   if kind=='gesture':
    result=dev.act(resolve_dynamic(dev,row['text']))
    assert bool(result.ok)==bool(row.get('ok')) and dev.st.tick==row['t']
   else:dev._tick(1)
   film.tick=dev.st.tick;film.files=[]
   if kind=='gesture':film.gesture(pre,dev,geo,None,slip=bool(row.get('slip')),ok=bool(result.ok))
   else:film.blocked(dev,geo,None)
   gestures[str(dev.st.tick)]={'frames':film.files.copy(),'fps':fh.FPS,'action':row['text']}
   print('ScreenSim gesture',dev.st.tick,len(film.files),'frames',flush=True)
 assert bool(task.goal(dev.st)[0])==record['goal_ok'] and dev.st.tick==record['final_tick']
 path=SITE/'data/mobile.json';e=json.loads(path.read_text())
 e['presentation']={'gestures':gestures,'description':'Touch gestures and page transitions reconstructed with ScreenSim’s filming renderer. Action outcomes and the final goal are verified against the recorded episode.'}
 # Allocate gesture time before speech. Both films and the browser share this timeline.
 elapsed=0
 for seg in e['playback']['segments']:
  tick=seg['tick'];g=gestures.get(str(tick));duration=len(g['frames'])/g['fps'] if g else 0
  seg['start']=elapsed;seg['gestureDuration']=duration
  ds=[d for d in e['dialogue'] if d['tick']==tick];offset=elapsed+duration
  for d in ds:d['start']=offset;offset+=d['duration']+.25
  seg['duration']=max(5 if tick==e['ticks'] else .45,offset-elapsed,duration+.2)
  elapsed+=seg['duration']
 e['playback']['duration']=elapsed;path.write_text(json.dumps(e,ensure_ascii=False))
 print('ScreenSim verified presentation complete',flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('engine',choices=['cooking','mobile']);a=p.parse_args()
 (cook if a.engine=='cooking' else mobile)()
