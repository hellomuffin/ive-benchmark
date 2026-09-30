"""Create standalone, voiced episode films with new observation/dialogue/progress UI."""
from pathlib import Path
import json,math,subprocess,wave
import numpy as np
from functools import lru_cache
from PIL import Image,ImageDraw,ImageFont,ImageOps
ROOT=Path(__file__).resolve().parents[1]; SITE=ROOT/'site';WORK=ROOT/'.work'
if not SITE.exists() and (ROOT.parent/'docs').exists():SITE=ROOT.parent/'docs'
FONT=SITE/'assets/fonts/font-0.woff2'
W,H,FPS=1600,1000,10
INK='#18353b';MUT='#71817c';TEAL='#27796d';BG='#f6f6ef';LINE='#d8e0d5'
@lru_cache(maxsize=32)
def font(n):return ImageFont.truetype(str(FONT),n)
@lru_cache(maxsize=2048)
def wrap(text,f,w):
 lines=['']
 for word in text.split():
  s=(lines[-1]+' '+word).strip()
  if f.getlength(s)>w and lines[-1]:lines.append(word)
  else:lines[-1]=s
 return lines
def put(d,xy,text,size=20,fill=INK,width=None,spacing=7):
 f=font(size);lines=wrap(text,f,width) if width else [text]
 for i,l in enumerate(lines):d.text((xy[0],xy[1]+i*(size+spacing)),l,font=f,fill=fill)
 return len(lines)*(size+spacing)
def panel(d,box,fill=BG):d.rounded_rectangle(box,12,fill=fill,outline=LINE,width=1)
def pastefit(im,src,box):
 fitted=ImageOps.contain(src,(box[2]-box[0],box[3]-box[1]),Image.Resampling.LANCZOS)
 im.paste(fitted,(box[0]+(box[2]-box[0]-fitted.width)//2,box[1]+(box[3]-box[1]-fitted.height)//2))
def render(e,tick,sec,frames):
 im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
 put(d,(40,24),'ive',44,TEAL);put(d,(130,35),'INTERACTIVE VISUAL EVALUATION',16)
 put(d,(1160,35),e['engine']+'  /  '+e['model'],16)
 d.line((40,88,1560,88),fill=LINE,width=2)
 put(d,(40,107),'THE TASK',13,TEAL);put(d,(40,135),e['task'],23,width=1130)
 put(d,(1250,111),'SIMULATED USER',13,TEAL);put(d,(1250,140),e['persona'],19,width=295)
 y=208
 labels=['Skill','Trust in AI','Pace','Alert tolerance','Interruption']
 levels=[['Novice','Intermediate','Expert'],['Low','Medium','High'],['Cautious','Balanced','Fast'],['Strict','Balanced','Broad'],['Step-by-step','Balanced','Avoid']]
 for i,n in enumerate(e['axes']):
  x=40+i*306;put(d,(x,y),labels[i],13,MUT);put(d,(x+125,y),levels[i][n-1],13,TEAL)
  for k in range(3):d.rounded_rectangle((x+k*90,y+28,x+k*90+82,y+33),2,fill=TEAL if k==n-1 else LINE)
 panel(d,(40,268,860,824),'#e9eee5');panel(d,(880,268,1560,824),'#fffefa')
 put(d,(60,284),'USER OBSERVATION',13,TEAL);put(d,(710,284),f'TICK {tick:03d}',13,MUT)
 put(d,(900,284),'THE CONVERSATION',13,TEAL);put(d,(1340,284),'SYNTHETIC VOICES',11,MUT)
 src=frames[min(tick,len(frames)-1)]
 if e['id']=='mobile':pastefit(im,src,(70,319,825,756))
 else:
  crops=e['crops'];x,y,w,h=crops['main'];pastefit(im,src.crop((x,y,x+w,y+h)),(60,316,838,690))
  x,y,w,h=crops['context'];pastefit(im,src.crop((x,y,x+w,y+h)),(60,695,258,780))
  put(d,(278,705),'TOP-DOWN VIEW',12,TEAL);put(d,(278,733),'Same world. Same moment.',15,MUT)
 actions=[a for a in e['actions'] if a['start']<=tick]
 action=actions[-1]['text'] if actions else 'Observe the environment'
 d.rectangle((41,785,859,823),fill='#dae5d9');put(d,(60,795),'ACTION',11,TEAL);put(d,(130,793),action,15,width=710)
 msgs=[m for m in e['dialogue'] if m['start']<=sec];blocks=[];used=0
 for m in reversed(msgs):
  lines=wrap(m['text'],font(20),590);height=61+len(lines)*27
  if used+height>476 and blocks:break
  blocks.insert(0,(m,lines,height));used+=height+12
 yy=327
 if not blocks:put(d,(960,470),'The user begins the task.\nThe assistant observes.',23,MUT,width=510)
 for m,lines,h in blocks:
  user=m['speaker']=='user';xx=920 if user else 900
  # Subtle entrance motion, without modifying the observed state.
  yy2=yy+int(max(0,.35-(sec-m['start']))*22)
  d.rounded_rectangle((xx,yy2,1540,yy2+h),9,fill='#f0ede3' if user else '#e4eee7')
  put(d,(xx+16,yy2+13),('SIMULATED USER' if user else e['model'].upper())+f' · TICK {m["tick"]}',11,'#867443' if user else TEAL)
  for j,line in enumerate(lines):put(d,(xx+16,yy2+37+j*27),line,20)
  yy+=h+12
 put(d,(40,851),'TASK PROGRESS',12,TEAL)
 n=len(e['milestones']);mw=790/n
 for i,m in enumerate(e['milestones']):
  x=40+i*mw;done=tick>=m['tick'];d.rounded_rectangle((x,879,x+mw-10,885),2,fill=TEAL if done else LINE)
  put(d,(x,898),m['label'],13,TEAL if done else MUT,width=mw-15)
 put(d,(880,851),'SCHEDULED EVENTS',12,TEAL)
 active=[v for v in e['events'] if v['tick']<=tick]
 if active:
  ev=max(active,key=lambda x:x['tick']);credited=ev.get('detected') and tick>=(ev.get('detectedAt') or ev.get('end') or tick+1)
  panel(d,(880,879,1560,934),'#e5eee2' if credited else '#f8ecd8');put(d,(899,893),f'Tick {ev["tick"]}  ·  '+ev['label'],17,'#356644' if credited else '#875923')
  if credited:put(d,(1400,902),'Flag credited',11,'#356644')
 else:put(d,(880,888),'No scheduled event has triggered yet.',17,MUT)
 d.line((40,958,1560,958),fill=LINE)
 put(d,(40,971),'Recorded interaction · added presentation voices · time-expanded playback',12,MUT)
 if tick==e['ticks']:
  d.rounded_rectangle((590,705,820,757),9,fill=TEAL);put(d,(612,720),'✓ Goal satisfied',20,'white')
 progress=sec/e['playback']['duration'];d.rectangle((1100,975,1560,979),fill=LINE);d.rectangle((1100,975,1100+460*progress,979),fill=TEAL)
 return im

def export(key):
 WORK.mkdir(exist_ok=True)
 e=json.loads((SITE/f'data/{key}.json').read_text());assert all('audio' in d for d in e['dialogue'])
 frames=[Image.open(p).convert('RGB') for p in sorted((SITE/f'assets/media/{key}').glob('*.jpg'))]
 duration=e['playback']['duration'];dest=SITE/f'assets/media/{key}.mp4';temp=WORK/f'{key}-silent.mp4'
 rate=24000;waveform=np.zeros(math.ceil((duration+1)*rate),dtype=np.int32)
 for m in e['dialogue']:
  audio_path=SITE/m['audio']
  if audio_path.suffix=='.wav':
   with wave.open(str(audio_path)) as f:pcm=f.readframes(f.getnframes())
  else:
   pcm=subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-i',str(audio_path),'-f','s16le','-ac','1','-ar',str(rate),'-'],check=True,capture_output=True).stdout
  sample=np.frombuffer(pcm,dtype='<i2').astype(np.int32)
  start=round(m['start']*rate);waveform[start:start+len(sample)]+=sample
 wav=WORK/f'{key}-mix.wav'
 with wave.open(str(wav),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate);f.writeframes(np.clip(waveform,-32768,32767).astype('<i2').tobytes())
 proc=subprocess.Popen(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','22','-pix_fmt','yuv420p',str(temp)],stdin=subprocess.PIPE)
 idx=0;segments=e['playback']['segments']
 for fi in range(math.ceil(duration*FPS)):
  sec=fi/FPS
  while idx<len(segments)-1 and sec>=segments[idx+1]['start']:idx+=1
  frame=render(e,segments[idx]['tick'],sec,frames)
  if fi==min(250,math.floor(duration*FPS/2)):frame.save(SITE/f'assets/media/{key}.jpg')
  proc.stdin.write(frame.tobytes())
  if fi%500==0:print(key,fi,'/',math.ceil(duration*FPS),flush=True)
 proc.stdin.close();assert proc.wait()==0
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(temp),'-i',str(wav),'-c:v','copy','-c:a','aac','-b:a','128k','-shortest','-movflags','+faststart',str(dest)],check=True)
 print('Exported',dest.name,round(duration,1),'seconds',flush=True)
if __name__=='__main__':
 import sys
 for key in (sys.argv[1:] or ['cooking','household','mobile']):export(key)
