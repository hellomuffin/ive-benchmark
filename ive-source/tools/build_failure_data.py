"""Trace the paper's qualitative figure to the original episode and exact ticks."""
import json,shutil,subprocess
from pathlib import Path
from PIL import Image
from build_data import ROOT, WORKSPACE as WS, PUBLIC as SITE, common, dump
from build_comparison_data import conversation

def main():
 specs=[('failure-delay','VHSim','Gemini 3.1 Pro','Fast, low-trust user',[2,1,3,2,3],
 'Collect three plates and two glasses into the dishwasher, then close it.',
 'vh-streaming-engine/tmp/bench_v1/gemini-3.1-pro-preview/gemini-3.1-pro-preview__cx_dishes_missing_stall__speed_demon.json',360,385),
 ('failure-interrupt','CookSim','GPT-Realtime 2.1','Independent expert',[3,1,2,1,3],
 'Prepare a Loaded Burrito: tortilla, rice, steak, tomato, and lettuce.',
 'cook-bench-engine/tmp/sample_r6_compare/frames/classic_expert/gpt-realtime-2.1__before_fix/b3_master_nops_hard_map_2.json',0,16)]
 for key,engine,model,persona,axes,task,path,start,end in specs:
  r=json.loads((WS/path).read_text());e=common(key,engine,model,persona,axes,task,r,path)
  e.update(clip={'start':start,'end':end},ticks=r['ticks'],dialogue=[c for c in conversation(r) if start<=c['tick']<=end],
    actions=[{'start':a['t_issue'],'end':a.get('t_done') or a['t_issue'],'text':a['cmd']} for a in r.get('actions',r.get('action_log',[])) if a['t_issue']<=end and (a.get('t_done') or a['t_issue'])>=start],
    events=[],milestones=[],quality={'overall':None,'categories':{},'rounds':[]})
  folder=SITE/f'assets/media/{key}';folder.mkdir(exist_ok=True)
  if engine=='VHSim':
   subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(start),'-i',str((WS/path).with_suffix('.mp4')),'-t',str(end-start+1),'-vf','fps=1','-q:v','3','-start_number',str(start),str(folder/'%04d.jpg')],check=True)
   e['crops']={'main':[0,24,640,456],'context':[640,24,480,456]}
   e['annotations']=[{'start':370,'end':375,'text':'Assistant response pending · the user continues acting'},
    {'start':376,'end':385,'text':'Guidance arrives after the plate has been collected'}]
  else:
   source=WS/'experiment/07_assistant_failure_modes/example_gpt-realtime-2.1_before_fix_b3_master_nops_hard_map_2_first30/frames'
   for tick in range(start,end+1):shutil.copy2(source/f't{tick:02d}.jpg',folder/f'{tick:04d}.jpg')
   with Image.open(folder/'0000.jpg') as im:w,h=im.size
   # Inspect the actual frame headers: TOP-DOWN left, FIRST PERSON right.
   # These archived 1922x771 frames include a 51px header and 720px views.
   assert (w,h)==(1922,771)
   e['crops']={'main':[962,51,960,720],'context':[0,51,960,720]}
   e['annotations']=[{'start':3,'end':16,'text':'User is already walking to the pot · action completes at tick 18'}]
  e['frameCount']=end+1
  e['presentation']={'description':'Original recorded observations. The displayed excerpt preserves the original actions and dialogue.'}
  dump(SITE/f'data/{key}.json',e)
 print('Paper failure excerpts exported with original tick indices.')

if __name__=='__main__':main()
