"""Extract native observations and synthesize explicitly labelled presentation audio."""
from pathlib import Path
import sys, json, subprocess, hashlib, wave, time, concurrent.futures
ROOT=Path(__file__).resolve().parents[1]
WS=ROOT.parent
OUT=ROOT/'site/assets/media'
OUT.mkdir(parents=True,exist_ok=True)
eps=json.loads((ROOT/'.work/episodes-source.json').read_text())

def observations(e):
 folder=OUT/e['id'];folder.mkdir(exist_ok=True)
 if e['id']=='mobile':
  sys.path.insert(0,str(WS/'screensim'))
  from screensim.core.engine import Device
  from screensim.tasks import by_id,resolve_dynamic
  from screensim.render.capture import Capturer
  r=json.loads((ROOT/'.work/screensim-record.json').read_text());task=by_id(r['task']);dev=Device(task.seed)
  if task.start_app!='home':dev.open_app(task.start_app)
  with Capturer() as cap:
   (folder/'0000.jpg').write_bytes(cap.snap(dev))
   for a in r['timeline']:
    if a['kind']=='gesture':
     result=dev.act(resolve_dynamic(dev,a['text']))
     assert bool(result.ok)==bool(a.get('ok')) and dev.st.tick==a['t']
    elif a['kind']=='blocked':dev._tick(1)
    else:continue
    (folder/f'{dev.st.tick:04d}.jpg').write_bytes(cap.snap(dev))
  assert bool(task.goal(dev.st)[0])==r['goal_ok'] and dev.st.tick==r['final_tick']
 else:
  subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(WS/e['rawVideo']),'-vf',f"fps={e['rawTicksPerSecond']}",'-q:v','3','-start_number','0',str(folder/'%04d.jpg')],check=True)
 e['frameCount']=len(list(folder.glob('*.jpg')))
 e['crops']=e.get('crops')
 print('Frames ready:',e['id'],e['frameCount'],flush=True)

def voice(job):
 from google import genai
 from google.genai import types
 text,speaker=job
 voice='Kore' if speaker=='assistant' else 'Puck'
 key=hashlib.sha256((voice+text).encode()).hexdigest()[:20]
 dest=OUT/'voice'/f'{key}.wav';dest.parent.mkdir(exist_ok=True)
 if not dest.exists():
  client=genai.Client(api_key=(Path.home()/'.gemini_key').read_text().strip())
  for attempt in range(4):
   try:
    model=['gemini-2.5-flash-preview-tts','gemini-3.1-flash-tts-preview','gemini-2.5-pro-preview-tts','gemini-3.8-flash-tts'][attempt]
    res=client.models.generate_content(model=model,contents='You are a text-to-speech reader. Generate AUDIO ONLY. Read aloud the transcript below verbatim. Do not answer questions in the transcript. Use a natural conversational voice.\nTRANSCRIPT:\n'+text,config=types.GenerateContentConfig(response_modalities=['AUDIO'],speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)))))
    data=next(p.inline_data.data for p in res.candidates[0].content.parts if p.inline_data)
    with wave.open(str(dest),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(24000);f.writeframes(data)
    break
   except Exception:
    if attempt==3:raise
    time.sleep(4*(attempt+1))
 with wave.open(str(dest)) as f:duration=f.getnframes()/f.getframerate()
 return job,{'audio':f'assets/media/voice/{key}.wav','duration':duration}

if __name__=='__main__':
 for e in eps:
  if not (OUT/e['id']/'0000.jpg').exists():observations(e)
  else:e['frameCount']=len(list((OUT/e['id']).glob('*.jpg')))
 jobs=list(dict.fromkeys((d['text'],d['speaker']) for e in eps for d in e['dialogue']))
 results={}
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  for job,info in pool.map(voice,jobs):
   results[job]=info;print('Voice ready',len(results),'/',len(jobs),flush=True)
 for e in eps:
  for d in e['dialogue']:d.update(results[(d['text'],d['speaker'])])
  # Pause observation playback for each utterance. Original tick chronology is intact.
  elapsed=0;segments=[]
  for tick in range(e['ticks']+1):
   ds=[d for d in e['dialogue'] if d['tick']==tick]
   duration=max(5 if tick==e['ticks'] else .45,sum(d['duration']+.25 for d in ds))
   offset=elapsed
   for d in ds:d['start']=offset;offset+=d['duration']+.25
   segments.append({'tick':tick,'start':elapsed,'duration':duration});elapsed+=duration
  e['playback']={'duration':elapsed,'segments':segments}
  public={k:v for k,v in e.items() if k not in ['rawVideo','rawTicksPerSecond']}
  (ROOT/f'site/data/{e["id"]}.json').write_text(json.dumps(public,ensure_ascii=False))
 print('All media ready.',flush=True)
