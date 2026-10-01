const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const axisNames = ['Skill','Trust in AI','Pace','Alert tolerance','Interruption'];
const axisLevels = [['Novice','Intermediate','Expert'],['Low','Medium','High'],['Cautious','Balanced','Fast'],['Strict','Balanced','Broad'],['Step-by-step','Balanced','Avoid']];
const cache = new Map();
const players = new Set();
async function data(id) {
  if (!cache.has(id)) cache.set(id, fetch(`data/${id}.json`,{cache:'no-cache'}).then(r => {if(!r.ok)throw Error(`Episode unavailable: ${id}`);return r.json();}));
  return cache.get(id);
}
function axes(e,cls) {return `<div class="${cls}">${e.axes.map((n,i)=>`<span>${axisNames[i]} <b>${axisLevels[i][n-1]}</b></span>`).join('')}</div>`;}
function completed(e) {return e.completed ?? (e.outcome === 'Task completed' || e.outcome === 'won');}

class Replay {
  constructor(container,e,{persona=false,failure=false}={}) {
    this.e=e;this.container=container;this.elapsed=0;this.playing=false;this.last=0;this.audio=new Audio();this.currentAudio='';this.images=new Map();this.lastTick=-1;this.lastChat=-1;this.disposed=false;
    this.segments=e.playback?.segments ?? [];
    this.duration=e.playback?.duration ?? 0;
    this.phone=e.engine==='ScreenSim';
    const quality=e.quality?.overall;
    const metrics=e.metrics;
    const results=persona?`<div><label>Task outcome</label><strong class="${completed(e)?'completed':'incomplete'}">${completed(e)?'Completed':'Incomplete'}</strong></div><div><label>Simulation ticks</label><strong>${e.ticks}</strong></div>`:
      `<div><label>In-time success</label><strong class="${metrics?.inTimeSuccess?'completed':metrics?'incomplete':''}">${metrics?(metrics.inTimeSuccess?'Yes':'No'):'—'}</strong><small>${e.ticks} / ${metrics?.budget??'—'} ticks</small></div><div><label>Error detection</label><strong>${metrics?.triggered?`${(100*metrics.detected/metrics.triggered).toFixed(1)}%`:'—'}</strong><small>${metrics?.detected??'—'} / ${metrics?.triggered??'—'} triggered errors</small></div><div><label>Interaction quality</label><strong class="quality-score">${quality==null?'—':(quality*100).toFixed(1)}<span style="font-size:14px;font-weight:400"> / 100</span></strong><div class="score-track"><i style="width:${(quality??0)*100}%"></i></div></div>`;
    container.className=`recorded-replay${this.phone?' phone':''}`;
    container.innerHTML=`<div class="replay-title"><h3>${esc(persona?e.persona:e.model)}</h3><p>${esc(persona?e.model:failure?`${e.engine} · ticks ${e.clip.start}–${e.clip.end}`:e.persona)}</p></div>
      ${persona?axes(e,'persona-dials'):''}
      ${failure?'':`<div class="episode-results">${results}</div>`}
      <div class="replay-views"><div class="replay-view"><span>${this.phone?'Phone interface':'Egocentric view'}</span><canvas width="${this.phone?492:640}" height="${this.phone?940:480}" aria-label="${esc(e.model)} ${this.phone?'phone':'egocentric'} observation"></canvas></div>${this.phone?'':'<div class="replay-view"><span>Top-down view</span><canvas width="640" height="480" aria-label="Top-down observation"></canvas></div>'}</div>
      <div class="replay-action"><small>User action</small><b></b></div>
      <div class="replay-controls"><button class="replay-play" aria-label="Play ${esc(persona?e.persona:e.model)} episode">▶ Play</button><input type="range" min="0" max="${this.duration}" step=".1" value="0" aria-label="Seek ${esc(e.model)} episode"><output>Tick ${e.clip?.start??0}</output></div>
      ${failure?'<div class="replay-annotation"></div>':''}
      <div class="replay-chat" aria-label="Recorded conversation"></div>
      ${failure?'':'<details class="replay-rubric"><summary>Conversation-round evaluation <strong>—</strong></summary><div></div></details>'}
      ${failure?'':`<div class="replay-state"><h4>Task progress</h4><div class="progress-pills"></div><h4>Scheduled events</h4><div class="replay-events"></div></div>`}
      <div class="replay-links"><a href="data/${e.id}.json" download>Episode record ↓</a>${failure?`<a href="${e.media}" download>Video clip ↓</a>`:''}</div>`;
    this.$=s=>container.querySelector(s);
    this.canvases=[...container.querySelectorAll('canvas')];
    this.$('.replay-play').onclick=()=>this.playing?this.pause():this.play();
    this.$('input').oninput=event=>{this.elapsed=Number(event.target.value);this.audio.pause();this.currentAudio='';this.render();};
    this.render();players.add(this);
    this.observer=new IntersectionObserver(entries=>{if(!entries[0].isIntersecting)this.pause();},{threshold:0});this.observer.observe(container);
    this.animate=time=>{
      if(this.disposed)return;
      if(this.playing){this.elapsed=Math.min(this.duration,this.elapsed+(time-this.last)/1000);this.render();if(this.elapsed>=this.duration)this.pause();}
      this.last=time;this.raf=requestAnimationFrame(this.animate);
    };this.raf=requestAnimationFrame(this.animate);
  }
  play() {
    for(const p of players)if(p!==this)p.pause();
    if(this.elapsed>=this.duration)this.elapsed=0;
    this.playing=true;this.last=performance.now();this.$('.replay-play').textContent='Ⅱ Pause';this.render();
  }
  pause() {this.playing=false;this.audio.pause();this.$('.replay-play').textContent='▶ Play';}
  seek(tick) {this.pause();const segment=this.segments.find(s=>s.tick>=tick)??this.segments.at(-1);this.elapsed=(segment?.start??0)+.01;this.currentAudio='';this.render();}
  destroy(){this.pause();this.disposed=true;cancelAnimationFrame(this.raf);this.observer.disconnect();players.delete(this);}
  image(path) {
    if(!this.images.has(path)) {
      const img=new Image();this.images.set(path,img);img.onload=()=>{if(!this.disposed)this.frame();};img.src=path;
      if(this.images.size>35)this.images.delete(this.images.keys().next().value);
    }
    return this.images.get(path);
  }
  frame() {
    const e=this.e,t=this.tick??e.clip?.start??0,p=e.presentation??{};
    let path;
    const gesture=p.gestures?.[String(t)];
    if(gesture){const i=Math.max(0,Math.min(gesture.frames.length-1,Math.floor((this.elapsed-this.segment.start)*gesture.fps)));path=gesture.frames[i];}
    else path=`${p.frameRoot??`assets/media/${e.id}`}/${String(Math.min(t,(p.frameCount??e.frameCount)-1)).padStart(4,'0')}.jpg`;
    const img=this.image(path);if(!img?.complete || !img.naturalWidth)return;
    const crops=p.crops??e.crops;
    this.canvases.forEach((canvas,i)=>{
      const ctx=canvas.getContext('2d');ctx.fillStyle='#f3f5f8';ctx.fillRect(0,0,canvas.width,canvas.height);
      const [sx,sy,sw,sh]=this.phone?[0,0,img.naturalWidth,img.naturalHeight]:crops[i===0?'main':'context'];
      const scale=Math.min(canvas.width/sw,canvas.height/sh),w=sw*scale,h=sh*scale;
      ctx.drawImage(img,sx,sy,sw,sh,(canvas.width-w)/2,(canvas.height-h)/2,w,h);
    });
  }
  render() {
    const e=this.e;this.segment=this.segments.findLast(s=>s.start<=this.elapsed)??this.segments[0];
    this.tick=this.segment?.tick??e.clip?.start??0;const t=this.tick;
    this.$('input').value=this.elapsed;this.$('output').textContent=`Tick ${t}`;
    if(t!==this.lastTick){
      this.lastTick=t;
      const a=e.actions.filter(a=>a.start<=t).at(-1);
      this.$('.replay-action b').textContent=a?.text??'Observe the environment';
      const progress=this.$('.progress-pills');
      if(progress)progress.innerHTML=e.milestones.length?e.milestones.map(m=>`<span class="${t>=m.tick?'done':''}">${t>=m.tick?'✓ ':''}${esc(m.label)}</span>`).join(''):'Goal not yet satisfied';
      const events=this.$('.replay-events');
      if(events)events.innerHTML=e.events.map(ev=>{
        let status=t<ev.tick?'Scheduled':'Triggered',resolved=false;
        if(ev.answeredAt!=null&&t>=ev.answeredAt){status='Answered';resolved=true;}
        else if(ev.alertAt!=null&&t>=ev.alertAt){status='Alert delivered';resolved=true;}
        else if(ev.detected&&t>=(ev.detectedAt??ev.end??Infinity)){status='Error detected';resolved=true;}
        else if(ev.kind==='plan_change'&&t>=ev.tick){status='Goal changed';resolved=true;}
        return `<div class="replay-event ${resolved?'resolved':t>=ev.tick?'active':''}"><span>${esc(ev.label)}</span><small>${status}</small></div>`;
      }).join('');
      const annotation=this.$('.replay-annotation');if(annotation)annotation.textContent=e.annotations?.find(a=>t>=a.start&&t<=a.end)?.text??'The user acts while the assistant observes.';
    }
    this.frame();
    const dialogue=e.dialogue.filter(d=>(d.start??Infinity)<=this.elapsed);
    if(dialogue.length!==this.lastChat){
      this.lastChat=dialogue.length;const chat=this.$('.replay-chat');
      chat.innerHTML=dialogue.length?dialogue.map(d=>`<div class="replay-message ${d.speaker}"><small>${esc(d.speaker==='assistant'?e.model:'User')} · tick ${d.tick}</small>${esc(d.text)}</div>`).join(''):'<div class="replay-empty">No utterances yet.</div>';
      chat.scrollTop=chat.scrollHeight;
      const rubric=this.$('.replay-rubric');
      if(rubric){
        const lastAssistant=dialogue.filter(d=>d.speaker==='assistant').at(-1);
        const round=lastAssistant?e.quality.rounds.filter(r=>r.tick<=lastAssistant.tick).at(-1):null;
        rubric.querySelector('strong').textContent=round?`${(round.score*100).toFixed(1)} / 100`:'—';
        rubric.querySelector('div').innerHTML=round?`<p>Conversation round beginning at tick ${round.tick}.</p>`+round.evidence.map(x=>`<p><b>${esc(x.id)} · ${x.pass==null?'Not applicable':x.pass?'Pass':'Fail'}</b> ${esc(x.reason)}</p>`).join(''):'Evaluation appears when the assistant responds.';
      }
    }
    const active=e.dialogue.find(d=>this.elapsed>=d.start&&this.elapsed<d.start+d.duration);
    if(this.playing&&active?.audio){
      const key=`${active.audio}:${active.start}`;
      if(key!==this.currentAudio){this.currentAudio=key;this.audio.src=active.audio;this.audio.currentTime=Math.max(0,this.elapsed-active.start);this.audio.play().catch(()=>{});}
      else if(this.audio.paused)this.audio.play().catch(()=>{});
    }else{this.audio.pause();if(!active)this.currentAudio='';}
  }
}

let currentPair=[],generation=0;
async function showPair(manifest,id){
  const gen=++generation;const pair=manifest.comparisons.find(x=>x.id===id)??manifest.comparisons[0];
  const episodes=await Promise.all(pair.episodes.map(data));if(gen!==generation)return;
  for(const p of currentPair)p.destroy();
  const host=document.querySelector('#matched-comparison');
  host.innerHTML=`<div class="comparison-context"><span class="eyebrow">Same episode settings · different assistants</span><h3>${esc(episodes[0].task)}</h3>${axes(episodes[0],'shared-persona')}</div><div class="replay-grid"></div><div class="paired-rubrics"><h4>Interaction quality by dimension</h4><div class="paired-rubric-grid">${['Factual grounding','Situational relevance','Actionable guidance','User intent uptake','Guidance conciseness'].map((name,i)=>{const key=['truthful','sensible','helpful','listens','economy'][i];return `<div><h5>${name}</h5>${episodes.map((e,j)=>{const raw=e.quality.categories[key],v=(raw??0)*100,label=raw==null?'N/A':v.toFixed(1);return `<div class="paired-bar model-${j}" title="${esc(e.model)}: ${raw==null?'Not applicable':label}"><i style="width:${v}%"></i><span>${label}</span></div>`;}).join('')}</div>`;}).join('')}</div><p>Top: ${esc(episodes[0].model)} · Bottom: ${esc(episodes[1].model)} · N/A: no applicable rubric items.</p></div><p class="comparison-note">Scores describe these recorded episodes, not benchmark averages. Playback preserves simulation ticks; synthetic speech expands presentation time. Play either trajectory to hear its conversation.</p>`;
  currentPair=episodes.map(e=>{const node=document.createElement('article');host.querySelector('.replay-grid').append(node);return new Replay(node,e);});
  const jumps=document.createElement('div');jumps.className='comparison-jumps';
  for(const [label,getTick] of [['Start',()=>0],['First scheduled error',e=>e.events.find(x=>x.kind==='error')?.tick??0],['Final state',e=>e.ticks]]){
    const button=document.createElement('button');button.textContent=label;button.onclick=()=>currentPair.forEach(p=>p.seek(getTick(p.e)));jumps.append(button);
  }
  host.querySelector('.comparison-context').append(jumps);
}

async function init(){
  const manifest=await data('comparisons');
  document.querySelectorAll('[data-episode]').forEach(b=>{
    const labels={cooking:'Cooking',household:'Household activities',mobile:'Mobile interface use'};
    b.querySelector('small').textContent=labels[b.dataset.episode];
    b.addEventListener('click',()=>showPair(manifest,b.dataset.episode));
  });
  await showPair(manifest,new URLSearchParams(location.search).get('episode')??'cooking');
  const failures=[
    ['failure-delay','Guidance becomes outdated while the assistant responds.','The user collects the plate before the instruction to fetch it arrives.'],
    ['failure-interrupt','Repeated guidance interrupts an action already underway.','The assistant repeats instructions during a long walk, despite the user’s preference for minimal interruptions.']
  ];
  const fh=document.querySelector('#recorded-failures');fh.className='replay-grid';
  for(const [id,title,description] of failures){
    const e=await data(id),block=document.createElement('div');
    block.innerHTML=`<div class="failure-intro"><h3>${esc(title)}</h3><p class="failure-explanation">${esc(description)}</p></div><article></article>`;
    fh.append(block);new Replay(block.querySelector('article'),e,{failure:true});
  }
  fh.insertAdjacentHTML('afterend','<p class="comparison-note">Excerpts from the paper’s qualitative examples. Dialogue and actions are from the original recordings; speech is synthetic.</p>');
  const ph=document.querySelector('#persona-replays');ph.innerHTML=`<div class="comparison-context"><span class="eyebrow">CookSim · GPT-6 Astra</span><h3>${esc(manifest.personas.task)}</h3></div><div class="replay-grid persona-grid"></div><p class="comparison-note">All three users complete the recipe. These selected trajectories illustrate persona-conditioned behavior; they are not aggregate measures of user-simulation fidelity.</p>`;
  const personaPlayers=[];
  for(const id of manifest.personas.episodes){const e=await data(id),node=document.createElement('article');ph.querySelector('.persona-grid').append(node);personaPlayers.push(new Replay(node,e,{persona:true}));}
  const jumps=document.createElement('div');jumps.className='comparison-jumps';
  for(const [label,ticks] of [['Starting the task',[0,0,0]],['Guidance and user response',[110,147,134]]]){
    const button=document.createElement('button');button.textContent=label;button.onclick=()=>personaPlayers.forEach((p,i)=>p.seek(ticks[i]));jumps.append(button);
  }
  ph.querySelector('.comparison-context').append(jumps);
}
init().catch(error=>{console.error(error);document.querySelector('#matched-comparison').textContent='The recorded comparisons could not be loaded. Please refresh the page.';});
