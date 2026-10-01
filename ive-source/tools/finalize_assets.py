from pathlib import Path
import json,subprocess
from PIL import Image,ImageOps
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'site'
def stamp(t):
 ms=round(t*1000);return f'{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d}.{ms%1000:03d}'
for key in ['cooking','household','mobile']:
 path=SITE/f'data/{key}.json';e=json.loads(path.read_text());vtt=['WEBVTT','']
 for i,d in enumerate(e['dialogue']):
  vtt.extend([str(i+1),f'{stamp(d["start"])} --> {stamp(d["start"]+d["duration"])}',f'{e["model"] if d["speaker"]=="assistant" else "Simulated user"}: {d["text"]}',''])
  src=SITE/d['audio'];mp3=src.with_suffix('.mp3')
  if not mp3.exists():subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(src),'-codec:a','libmp3lame','-b:a','96k',str(mp3)],check=True)
  d['audio']=str(mp3.relative_to(SITE))
 (SITE/f'assets/media/{key}.vtt').write_text('\n'.join(vtt))
 path.write_text(json.dumps(e,ensure_ascii=False))
 # Clean environment thumbnails without small renderer labels or transcript UI.
 tick={'cooking':56,'household':65,'mobile':9}[key]
 pres=e.get('presentation',{});folder=SITE/pres.get('frameRoot',f'assets/media/{key}')
 with Image.open(folder/f'{tick:04d}.jpg') as im:
  if key=='mobile':thumb=im.crop((0,70,412,500))
  else:
   x,y,w,h=pres.get('crops',e['crops'])['context' if key=='cooking' else 'main']
   thumb=im.crop((x,y,x+w,y+h))
  ImageOps.fit(thumb.convert('RGB'),(360,210),method=Image.Resampling.LANCZOS).save(SITE/f'assets/media/{key}-thumb.jpg',quality=92)
print('Created timed transcripts and compressed browser audio.')
