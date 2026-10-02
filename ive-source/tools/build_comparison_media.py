"""Native recorded frames and verbatim, explicitly synthetic presentation speech."""
from pathlib import Path
import json,sys,subprocess,concurrent.futures
from build_media import voice
from build_data import ROOT, WORKSPACE as WS, PUBLIC as SITE, dump

def observations(e):
 folder=SITE/f'assets/media/{e["id"]}';folder.mkdir(exist_ok=True)
 if e['engine']=='ScreenSim':
  sys.path.insert(0,str(WS/'screensim'))
  from screensim.core.engine import Device
  from screensim.tasks import by_id,resolve_dynamic,S
  from screensim.render.capture import Capturer
  r=json.loads((ROOT/f'.work/{e["id"]}-record.json').read_text());task=by_id(r['task']);dev=Device(task.seed)
  if task.start_app!='home':dev.open_app(task.start_app)
  found={}
  with Capturer() as cap:
   (folder/'0000.jpg').write_bytes(cap.snap(dev))
   for a in r['timeline']:
    if a['kind']=='gesture':
     result=dev.act(resolve_dynamic(dev,a['text']))
     assert bool(result.ok)==bool(a.get('ok')) and dev.st.tick==a['t']
    elif a['kind']=='blocked':dev._tick(1)
    else:continue
    (folder/f'{dev.st.tick:04d}.jpg').write_bytes(cap.snap(dev))
    state=S(dev.st);app=state['apps']['TripSnap']
    for label,ok in [('Location: Never',app['loc_mode']=='Never'),('Background refresh off',not app['bg']),('Tracking off',not app['track'] and state['spec']['priv']['tracking'])]:
     if ok and label not in found:found[label]=dev.st.tick
     if not ok:found.pop(label,None)
  assert bool(task.goal(dev.st)[0])==r['goal_ok']
  e['milestones']=[{'label':label,'tick':tick} for label,tick in found.items()]
 elif not (folder/'0000.jpg').exists():
  video=(WS/e['source']).with_suffix('.mp4')
  subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(video),'-vf',f"fps={6 if e['engine']=='CookSim' else 1}",'-q:v','3','-start_number','0',str(folder/'%04d.jpg')],check=True)
 e['frameCount']=len(list(folder.glob('*.jpg')))
 assert e['frameCount']>0

def main(keys):
 episodes=[json.loads((SITE/f'data/{k}.json').read_text()) for k in keys]
 for e in episodes:
  if not e.get('clip'):observations(e)
  dump(SITE/f'data/{e["id"]}.json',e)
 jobs=list(dict.fromkeys((d['text'],d['speaker']) for e in episodes for d in e['dialogue']))
 results={}
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  for job,info in pool.map(voice,jobs):
   wav=SITE/info['audio'];mp3=wav.with_suffix('.mp3')
   if not mp3.exists():subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(wav),'-b:a','96k',str(mp3)],check=True)
   info['audio']=str(mp3.relative_to(SITE));results[job]=info
   print('Speech',len(results),'/',len(jobs),flush=True)
 for e in episodes:
  for d in e['dialogue']:d.update(results[(d['text'],d['speaker'])])
  elapsed=0;segments=[]
  start=e.get('clip',{}).get('start',0);end=e.get('clip',{}).get('end',e['ticks'])
  for tick in range(start,end+1):
   ds=[d for d in e['dialogue'] if d['tick']==tick];offset=elapsed
   for d in ds:d['start']=offset;offset+=d['duration']+.25
   duration=max(4 if tick==end else .45,offset-elapsed)
   segments.append({'tick':tick,'start':elapsed,'duration':duration});elapsed+=duration
  e['playback']={'duration':elapsed,'segments':segments}
  # A concurrent HD render may have attached its presentation metadata.
  latest=json.loads((SITE/f'data/{e["id"]}.json').read_text())
  for field in ['presentation','metrics']:
   if latest.get(field):e[field]=latest[field]
  dump(SITE/f'data/{e["id"]}.json',e)
 print('Comparison media ready',flush=True)

if __name__=='__main__':main(sys.argv[1:])
