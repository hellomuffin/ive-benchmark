"""Render presentation films from recorded trajectories and labelled presentation media."""
from pathlib import Path
import json,math,subprocess,wave
from functools import lru_cache
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageOps
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'site';WORK=ROOT/'.work'
if not SITE.exists() and (ROOT.parent/'docs').exists():SITE=ROOT.parent/'docs'
FONT=SITE/'assets/fonts/font-0.woff2'
W,H=1920,1080
INK='#263750';MUT='#7b8aa0';BLUE='#315ea8';BG='#ffffff';LINE='#dce4ef';WASH='#f4f6fa'
@lru_cache(maxsize=64)
def font(n,bold=False):
 f=ImageFont.truetype(str(FONT),n)
 if bold:
  try:f.set_variation_by_axes([650])
  except (OSError,ValueError):pass
 return f
@lru_cache(maxsize=4096)
def wrap(text,size,width,bold=False):
 f=font(size,bold);lines=['']
 for word in text.split():
  line=(lines[-1]+' '+word).strip()
  if f.getlength(line)>width and lines[-1]:lines.append(word)
  else:lines[-1]=line
 return lines
def put(d,xy,text,size=20,fill=INK,width=None,bold=False,spacing=7):
 lines=wrap(text,size,width,bold) if width else [text]
 for i,line in enumerate(lines):d.text((xy[0],xy[1]+i*(size+spacing)),line,font=font(size,bold),fill=fill)
 return len(lines)*(size+spacing)
def panel(d,box,fill=BG):d.rounded_rectangle(box,10,fill=fill,outline=LINE,width=1)
def pastefit(im,src,box):
 fitted=ImageOps.contain(src,(box[2]-box[0],box[3]-box[1]),Image.Resampling.LANCZOS)
 im.paste(fitted,(box[0]+(box[2]-box[0]-fitted.width)//2,box[1]+(box[3]-box[1]-fitted.height)//2))
@lru_cache(maxsize=20)
def load_frame(path):return Image.open(path).convert('RGB')
def source_frame(e,tick,sec):
 presentation=e.get('presentation',{})
 gesture=presentation.get('gestures',{}).get(str(tick))
 if gesture:
  seg=e['playback']['segments'][tick]
  ix=max(0,min(len(gesture['frames'])-1,int((sec-seg['start'])*gesture['fps'])))
  return load_frame(str(SITE/gesture['frames'][ix]))
 folder=SITE/presentation.get('frameRoot',f'assets/media/{e["id"]}')
 n=min(tick,presentation.get('frameCount',e['frameCount'])-1)
 return load_frame(str(folder/f'{n:04d}.jpg'))
def event_status(ev,tick):
 if ev.get('answeredAt') is not None and tick>=ev['answeredAt']:return 'Answered'
 if ev.get('alertAt') is not None and tick>=ev['alertAt']:return 'Alert delivered'
 if ev.get('kind')=='plan_change' and tick>=ev.get('end',ev['tick']):return 'Goal revised'
 detection=ev.get('detectedAt') if ev.get('detectedAt') is not None else ev.get('end')
 if ev.get('detected') and detection is not None and tick>=detection:return 'Flag credited'
 return 'Triggered'
def render_mobile(e,tick,sec):
 im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
 put(d,(44,22),'IVE',38,BLUE,bold=True);put(d,(132,34),'Interactive Visual Evaluation',20)
 put(d,(1480,34),'ScreenSim  /  '+e['model'],20,MUT)
 d.line((44,84,1876,84),fill=LINE)
 panel(d,(44,110,656,1020),WASH)
 src=source_frame(e,tick,sec)
 if str(tick) in e.get('presentation',{}).get('gestures',{}):
  pastefit(im,src,(116,118,584,1010))
 else:pastefit(im,src,(138,141,530,987))
 put(d,(696,112),'TASK',13,BLUE,bold=True)
 put(d,(696,140),e['task'],24,width=1180,bold=True)
 put(d,(696,221),'SIMULATED USER',12,BLUE,bold=True);put(d,(855,217),e['persona'],18)
 labels=['Skill level','Trust in AI','Pace','Alert tolerance','Interruption']
 levels=[['Novice','Intermediate','Expert'],['Low','Medium','High'],['Cautious','Balanced','Fast'],['Strict','Balanced','Broad'],['Step-by-step','Balanced','Avoid']]
 for i,n in enumerate(e['axes']):
  x=696+i*238;put(d,(x,259),labels[i],12,MUT);put(d,(x,281),levels[i][n-1],15,BLUE,bold=True)
  for k in range(3):d.rounded_rectangle((x+k*66,310,x+k*66+60,314),2,fill='#6285ba' if k==n-1 else '#e5eaf2')
 panel(d,(696,340,1876,825))
 put(d,(718,356),'Conversation',17,BLUE,bold=True);put(d,(1774,358),f'Tick {tick:03d}',14,MUT)
 d.line((696,392,1876,392),fill=LINE)
 blocks=[];used=0
 for m in reversed([m for m in e['dialogue'] if m['start']<=sec]):
  lines=wrap(m['text'],23,1080);height=51+len(lines)*32
  if used+height>405 and blocks:break
  blocks.insert(0,(m,lines,height));used+=height+12
 y=410
 if not blocks:put(d,(725,435),'No utterances yet.',20,MUT)
 for m,lines,height in blocks:
  user=m['speaker']=='user';x=727 if user else 712
  d.rounded_rectangle((x,y,1860,y+height),8,fill='#f7f4ee' if user else '#eef3fb')
  put(d,(x+16,y+10),('Simulated user' if user else e['model'])+f' · tick {m["tick"]}',12,'#9a7b53' if user else '#6482ad',bold=True)
  for j,line in enumerate(lines):put(d,(x+16,y+34+j*32),line,23,'#675741' if user else '#344b69')
  y+=height+12
 actions=[a for a in e['actions'] if a['start']<=tick]
 panel(d,(696,841,1876,889),'#edf2f9');put(d,(714,856),'USER ACTION',11,MUT)
 put(d,(833,853),actions[-1]['text'] if actions else 'Observe the interface',17,width=1000)
 put(d,(696,914),'TASK PROGRESS',12,BLUE,bold=True)
 for i,m in enumerate(e['milestones']):
  x=696+i*220;done=tick>=m['tick'];d.rounded_rectangle((x,943,x+202,948),2,fill='#6488b5' if done else LINE)
  put(d,(x,960),m['label'],13,'#476b98' if done else MUT,width=208)
 put(d,(1404,914),'SCHEDULED EVENT',12,BLUE,bold=True)
 active=[ev for ev in e['events'] if ev['tick']<=tick]
 if active:
  ev=max(active,key=lambda v:v['tick']);put(d,(1404,941),ev['label'],16,width=472)
  put(d,(1404,991),f'Tick {ev["tick"]} · '+event_status(ev,tick),12,MUT)
 else:put(d,(1404,945),'No event triggered.',16,MUT)
 d.line((44,1038,1876,1038),fill=LINE)
 put(d,(44,1051),'Recorded trajectory · synthetic speech · reconstructed touch gestures · presentation time expanded',11,MUT)
 return im
def render(e,tick,sec):
 if e['id']=='mobile':return render_mobile(e,tick,sec)
 im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
 put(d,(44,22),'IVE',38,BLUE,bold=True)
 put(d,(132,34),'Interactive Visual Evaluation',20)
 label=f'{e["engine"]}  /  {e["model"]}'
 put(d,(W-44-font(20).getlength(label),34),label,20,MUT)
 d.line((44,84,1876,84),fill=LINE,width=1)
 put(d,(44,104),'TASK',13,BLUE,bold=True)
 put(d,(44,131),e['task'],25,width=1330,bold=True)
 put(d,(1440,104),'SIMULATED USER',13,BLUE,bold=True)
 put(d,(1440,134),e['persona'],22,width=420)
 labels=['Skill level','Trust in AI','Pace','Alert tolerance','Interruption preference']
 levels=[['Novice','Intermediate','Expert'],['Low','Medium','High'],['Cautious','Balanced','Fast'],['Strict','Balanced','Broad'],['Step-by-step','Balanced','Avoid']]
 for i,n in enumerate(e['axes']):
  x=44+i*370;put(d,(x,204),labels[i],13,MUT);put(d,(x+190,204),levels[i][n-1],13,BLUE,bold=True)
  for k in range(3):d.rounded_rectangle((x+k*105,231,x+k*105+98,235),2,fill='#6285ba' if k==n-1 else '#e5eaf2')
 src=source_frame(e,tick,sec)
 if e['id']=='mobile':
  # Phone and gesture at full height; remaining width goes to dialogue.
  observation_right=762;conversation_left=788
  panel(d,(44,260,762,904),WASH)
  put(d,(66,277),'Mobile interface',17,BLUE,bold=True)
  pastefit(im,src,(210,313,606,858))
  # The original phone is 412×892; the hand renderer adds a small margin.
 else:
  observation_right=1236;conversation_left=1260
  crops=e.get('presentation',{}).get('crops',e['crops'])
  for x,key,title in [(44,'main','Egocentric view'),(652,'context','Top-down view')]:
   panel(d,(x,260,x+584,850),WASH)
   put(d,(x+20,279),title,17,BLUE,bold=True)
   sx,sy,sw,sh=crops[key]
   pastefit(im,src.crop((sx,sy,sx+sw,sy+sh)),(x+12,325,x+572,807))
  panel(d,(44,866,1236,914),'#edf2f9')
 actions=[a for a in e['actions'] if a['start']<=tick]
 action=actions[-1]['text'] if actions else 'Observe the environment'
 if e['id']=='mobile':
  put(d,(66,867),'USER ACTION',11,MUT)
  put(d,(180,865),action,15,width=560)
 else:
  put(d,(62,882),'USER ACTION',11,MUT)
  put(d,(182,879),action,17,width=1020)
 panel(d,(conversation_left,260,1876,914))
 put(d,(conversation_left+20,279),'Conversation',17,BLUE,bold=True)
 tick_label=f'Tick {tick:03d}'
 put(d,(1856-font(14).getlength(tick_label),280),tick_label,14,MUT)
 d.line((conversation_left,315,1876,315),fill=LINE)
 msgs=[m for m in e['dialogue'] if m['start']<=sec]
 blocks=[];used=0;cw=1876-conversation_left;tw=cw-78
 for m in reversed(msgs):
  lines=wrap(m['text'],21,tw);height=52+len(lines)*29
  if used+height>558 and blocks:break
  assert height<=558,(e['id'],m['tick'],'Dialogue exceeds panel')
  blocks.insert(0,(m,lines,height));used+=height+13
 yy=334
 if not blocks:put(d,(conversation_left+28,360),'No utterances yet.',20,MUT)
 for m,lines,height in blocks:
  user=m['speaker']=='user';xx=conversation_left+(30 if user else 16)
  yy2=yy+int(max(0,.25-(sec-m['start']))*16)
  fill='#f7f4ee' if user else '#eef3fb'
  d.rounded_rectangle((xx,yy2,1860,yy2+height),8,fill=fill)
  put(d,(xx+15,yy2+11),('Simulated user' if user else e['model'])+f' · tick {m["tick"]}',12,'#9a7b53' if user else '#6482ad',bold=True)
  for j,line in enumerate(lines):put(d,(xx+15,yy2+35+j*29),line,21,'#675741' if user else '#344b69')
  yy+=height+13
 put(d,(44,947),'TASK PROGRESS',12,BLUE,bold=True)
 mw=1146/len(e['milestones'])
 for i,m in enumerate(e['milestones']):
  x=44+i*mw;done=tick>=m['tick']
  d.rounded_rectangle((x,975,x+mw-12,980),2,fill='#6488b5' if done else '#e5eaf2')
  put(d,(x,990),m['label'],13,'#476b98' if done else MUT,width=mw-15)
 active=[v for v in e['events'] if v['tick']<=tick]
 put(d,(1260,947),'SCHEDULED EVENT',12,BLUE,bold=True)
 if active:
  ev=max(active,key=lambda x:x['tick']);status=event_status(ev,tick)
  put(d,(1260,975),ev['label'],17,width=590)
  put(d,(1260,1007),f'Tick {ev["tick"]} · {status}',12,'#967139' if status=='Triggered' else '#59816b')
 else:put(d,(1260,980),'No event triggered.',17,MUT)
 d.line((44,1038,1876,1038),fill=LINE)
 note='Recorded trajectory · synthetic speech · presentation time expanded'
 if e.get('presentation'):note+=' · reconstructed visuals'
 put(d,(44,1051),note,11,MUT)
 progress=min(1,sec/e['playback']['duration'])
 d.rectangle((1460,1059,1876,1062),fill=LINE);d.rectangle((1460,1059,1460+416*progress,1062),fill='#6285ba')
 return im
def export(key):
 WORK.mkdir(exist_ok=True);load_frame.cache_clear()
 e=json.loads((SITE/f'data/{key}.json').read_text());assert all('audio' in d for d in e['dialogue'])
 duration=e['playback']['duration'];dest=SITE/f'assets/media/{key}.mp4';temp=WORK/f'{key}-silent.mp4';fps=20 if key=='mobile' else 10
 rate=24000;waveform=np.zeros(math.ceil((duration+1)*rate),dtype=np.int32)
 for m in e['dialogue']:
  path=SITE/m['audio']
  if path.suffix=='.wav':
   with wave.open(str(path)) as f:pcm=f.readframes(f.getnframes())
  else:pcm=subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-i',str(path),'-f','s16le','-ac','1','-ar',str(rate),'-'],check=True,capture_output=True).stdout
  sample=np.frombuffer(pcm,dtype='<i2').astype(np.int32);start=round(m['start']*rate)
  waveform[start:start+len(sample)]+=sample
 wav=WORK/f'{key}-mix.wav'
 with wave.open(str(wav),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate);f.writeframes(np.clip(waveform,-32768,32767).astype('<i2').tobytes())
 proc=subprocess.Popen(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(fps),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p',str(temp)],stdin=subprocess.PIPE)
 idx=0;segments=e['playback']['segments']
 for fi in range(math.ceil(duration*fps)):
  sec=fi/fps
  while idx<len(segments)-1 and sec>=segments[idx+1]['start']:idx+=1
  frame=render(e,segments[idx]['tick'],sec)
  if fi==min(250,math.floor(duration*fps/2)):frame.save(SITE/f'assets/media/{key}.jpg',quality=93)
  proc.stdin.write(frame.tobytes())
  if fi%500==0:print(key,fi,'/',math.ceil(duration*fps),flush=True)
 proc.stdin.close();assert proc.wait()==0
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(temp),'-i',str(wav),'-c:v','copy','-c:a','aac','-b:a','128k','-shortest','-movflags','+faststart',str(dest)],check=True)
 print('Exported',dest.name,round(duration,1),'seconds',flush=True)
if __name__=='__main__':
 import sys
 for key in (sys.argv[1:] or ['cooking','household','mobile']):export(key)
