from pathlib import Path
import json,subprocess
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
print('Created timed transcripts and compressed browser audio.')
