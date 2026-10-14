const $=s=>document.querySelector(s);
const episodes=await fetch('episodes.json').then(r=>{if(!r.ok)throw new Error('Episode data unavailable');return r.json()});
if(new URLSearchParams(location.search).has('embed'))document.body.classList.add('embedded');
let index=0,previousCue=null,lastTick=-1;
const videos=episodes.map(e=>{const v=document.createElement('video');v.src=e.video;v.preload='metadata';v.playsInline=true;v.poster=`media/${e.id}.jpg`;$('#media-sources').append(v);return v});
const posters=episodes.map(e=>{const img=new Image();img.src=`media/${e.id}.jpg`;img.onload=render;return img});
const viewContexts=[$('#world').getContext('2d'),$('#ego').getContext('2d')];
const previewContexts=[$('.left-preview canvas').getContext('2d'),$('.right-preview canvas').getContext('2d')];
const clock=t=>`${Math.floor((t+.001)/60)}:${String(Math.floor((t+.001)%60)).padStart(2,'0')}`;
function score(label,value,type,detail,tip){return `<div class="score ${type} ${value===null?'missing':''} ${type==='completion'&&value===0?'failed':''}" title="${tip??''}"><div class="dial"><svg viewBox="0 0 100 100" aria-hidden="true"><circle class="track" cx="50" cy="50" r="43"/><circle class="arc" cx="50" cy="50" r="43" pathLength="100" style="--value:${type==='completion'?value*100:value??0}"/></svg><div class="number">${value===null?'—':type==='completion'?(value?'✓':'×'):Number(value.toFixed(1))}${value!==null&&type!=='completion'?'<small>%</small>':''}</div></div><div class="score-label">${label}</div><div class="score-detail">${detail??''}</div></div>`}
function positionEvent(e,tick){
 const completed=e.steps.filter(s=>s.tick!==null).map(s=>s.tick).sort((a,b)=>a-b);
 const points=[{tick:0,pos:0},...completed.map((t,i)=>({tick:t,pos:(i+1)/e.steps.length})),{tick:e.ticks,pos:completed.length/e.steps.length}];
 const a=points.filter(p=>p.tick<=tick).at(-1)??points[0],b=points.find(p=>p.tick>tick)??points.at(-1);
 return b.tick===a.tick?a.pos:a.pos+(b.pos-a.pos)*(tick-a.tick)/(b.tick-a.tick);
}
function select(next,direction=1){
 videos[index].pause();index=(next+episodes.length)%episodes.length;const e=episodes[index],v=videos[index];previousCue=null;lastTick=-1;
 $('#engine').textContent=`${e.engine} simulator`;$('#task').textContent=e.task;$('#episode-card').setAttribute('aria-label',`${index+1} of ${episodes.length}: ${e.engine}`);
 $('#world-label').textContent=e.viewNames[0];$('#ego-label').textContent=e.viewNames[1];$('.views').classList.toggle('phone-views',e.id==='screen');
 e.views.forEach((crop,i)=>{const c=viewContexts[i].canvas;c.width=e.id==='screen'?crop[2]:640;c.height=e.id==='screen'?crop[3]:480});
 $('#scores').innerHTML=score('Task completion',e.success,'completion',e.outcome)+score('Interaction quality',e.quality,'quality',e.quality===null?'Not graded':'',e.qualityNote)+(e.qa===null?'':score('QA accuracy',e.qa,'qa','Includes proactive',e.qaNote));
 $('#score-note').textContent=e.quality===null?'— No matching rubric grade for this recording; no scheduled QA or proactive-request tests.':'';
 $('#milestones').innerHTML=e.steps.map((s,i)=>`<div class="milestone"><span class="step-dot">${i+1}</span><span class="step-label">${s.label}</span></div>`).join('');
 const used=[];
 $('#events').innerHTML=e.events.map((event,i)=>{let pos=Math.max(1,Math.min(99,positionEvent(e,event.tick)*100));while(used.some(p=>Math.abs(p-pos)<3)&&pos<96)pos+=3;used.push(pos);const kind=event.kind.startsWith('qa_')?'question':'mistake';const type=event.kind==='qa_proactive'?'Proactive request':kind==='question'?'Question':'Mistake';return `<button class="event-pin event-${kind}" style="left:${pos}%" data-event="${i}" aria-label="${type}: ${event.label}, tick ${event.tick}" title="${type}: ${event.label} · tick ${event.tick}${event.detail?' — '+event.detail.replaceAll('"','&quot;'):''}"><span class="event-label" style="--anchor:${pos<25?0:pos>75?100:50}%">${event.label}</span></button>`}).join('');
 $('#events').querySelectorAll('button').forEach(b=>b.onclick=()=>{const event=e.events[Number(b.dataset.event)];const s=e.segments.find(s=>s.tick>=event.tick);v.currentTime=s?.start??0;render()});
 $('#episode-tabs').innerHTML=episodes.map((x,i)=>`<button role="tab" aria-selected="${i===index}" data-index="${i}">${x.engine}</button>`).join('');
 $('#episode-tabs').querySelectorAll('button').forEach(b=>b.onclick=()=>select(Number(b.dataset.index),Number(b.dataset.index)>index?1:-1));
 $('.left-preview .preview-title').textContent=episodes[(index+2)%3].engine;$('.right-preview .preview-title').textContent=episodes[(index+1)%3].engine;
 for(const [selector,other] of [['.left-preview',episodes[(index+2)%3]],['.right-preview',episodes[(index+1)%3]]]){
  const preview=$(selector);
  if(!preview.querySelector('.preview-task')){const task=document.createElement('span');task.className='preview-task';preview.querySelector('.preview-title').after(task);const dialogue=document.createElement('span');dialogue.className='preview-dialogue';dialogue.innerHTML='<b></b><span></span>';preview.querySelector('canvas').after(dialogue)}
  preview.querySelector('.preview-task').textContent=other.task;
  const line=other.dialogue.find(d=>d.text?.length>25)??other.dialogue[0];
  preview.querySelector('.preview-dialogue b').textContent=line?.speaker==='user'?'User':`Assistant · ${other.assistant}`;
  preview.querySelector('.preview-dialogue span').textContent=line?.text??'';
 }
 $('.left-preview').setAttribute('aria-label',`Watch ${episodes[(index+2)%3].engine}`);$('.right-preview').setAttribute('aria-label',`Watch ${episodes[(index+1)%3].engine}`);
 $('#seek').max=e.duration;$('.film').classList.toggle('started',v.currentTime>0);$('#play').textContent='▶';$('#play').setAttribute('aria-label','Play episode');
 $('#episode-card').classList.remove('turn-left','turn-right');void $('#episode-card').offsetWidth;$('#episode-card').classList.add(direction>0?'turn-right':'turn-left');
 if(v.readyState<2)v.load();render();notifySize();
}
function drawView(ctx,source,crop){if(!source || (source instanceof HTMLImageElement&&!source.naturalWidth))return;try{const w=ctx.canvas.width,h=ctx.canvas.height,s=Math.min(w/crop[2],h/crop[3]);ctx.fillStyle='#0d1018';ctx.fillRect(0,0,w,h);ctx.drawImage(source,...crop,(w-crop[2]*s)/2,(h-crop[3]*s)/2,crop[2]*s,crop[3]*s)}catch{}}
function drawPreview(ctx,j){const e=episodes[j],v=videos[j],source=v.readyState>=2?v:posters[j];ctx.fillStyle='#e5eef5';ctx.fillRect(0,0,640,360);if(!source)return;try{if(e.id==='screen'){ctx.drawImage(source,0,0,460,930,231,0,178,360)}else{const a=e.views[0],b=e.views[1];ctx.drawImage(source,...a,0,60,319,240);ctx.drawImage(source,...b,321,60,319,240)}}catch{}}
function render(){
 const e=episodes[index],v=videos[index],time=v.currentTime;let tick=e.segments.filter(s=>s.start<=time+.001).at(-1)?.tick??0;if(v.ended||time>=e.duration-.15)tick=e.ticks;
 const src=v.readyState>=2?v:posters[index];e.views.forEach((crop,i)=>{if(e.id==='screen'&&i===1){const y=tick<2?300:tick<4?65:tick<9?210:80;viewContexts[i].canvas.width=412;viewContexts[i].canvas.height=380;drawView(viewContexts[i],src,[24,y,412,380])}else drawView(viewContexts[i],src,crop)});drawPreview(previewContexts[0],(index+2)%3);drawPreview(previewContexts[1],(index+1)%3);
 const d=e.dialogue.filter(d=>d.start<=time).at(-1);
 if(d!==previousCue){previousCue=d;$('#speaker-name').textContent=d?.speaker==='user'?'User':'Assistant';$('#speaker-detail').textContent=d?.speaker==='user'?e.persona:e.assistant;$('.speech').classList.toggle('user',d?.speaker==='user');$('#utterance').replaceChildren();(d?.text??'').split(/\s+/).forEach((word,i)=>{const span=document.createElement('span');span.textContent=(i?' ':'')+word;$('#utterance').append(span)})}
 if(!d){$('#speaker-detail').textContent=e.assistant;$('#utterance').textContent='';}
 if(d)[...$('#utterance').children].forEach((w,i)=>w.classList.toggle('future',time<d.start+(d.words[i]?.start??0)));
 $('.speech').classList.toggle('is-speaking',!!d&&!v.paused&&time<d.start+d.duration);
 if(tick!==lastTick){lastTick=tick;$('#tick').textContent=`Tick ${tick} / ${e.ticks}`;let active=false;$('#milestones').querySelectorAll('.milestone').forEach((node,i)=>{const done=e.steps[i].tick!==null&&tick>=e.steps[i].tick;node.classList.toggle('done',done);node.classList.toggle('active',!done&&!active);if(!done)active=true;node.querySelector('.step-dot').textContent=done?'✓':i+1});const latest=e.events.filter(x=>x.tick<=tick).at(-1);$('#event-status').textContent=latest?`${latest.label}${tick<=latest.end?' · triggered':''}`:'Scheduled along task progress';$('#events').querySelectorAll('button').forEach((node,i)=>{const ev=e.events[i];node.classList.toggle('current',ev===latest);node.classList.toggle('triggered',tick>=ev.tick);node.classList.toggle('active',tick>=ev.tick&&tick<=ev.end)})}
 $('#seek').value=time;$('#timestamp').textContent=`${clock(time)} / ${clock(e.duration)}`;
}
async function toggle(){const v=videos[index];if(v.paused){if(v.ended)v.currentTime=0;try{await v.play();$('.film').classList.add('started')}catch{$('#utterance').textContent='Video is loading. Please try play again.'}}else v.pause();render()}
videos.forEach((v,i)=>{v.addEventListener('loadeddata',render);v.addEventListener('seeked',render);v.addEventListener('ended',()=>{render();$('#play').textContent='↻';$('#play').setAttribute('aria-label','Replay episode')});v.addEventListener('play',()=>{if(i===index){$('#play').textContent='Ⅱ';$('#play').setAttribute('aria-label','Pause episode')}});v.addEventListener('pause',()=>{if(i===index){$('#play').textContent='▶';$('#play').setAttribute('aria-label','Play episode');render()}})});
$('#play').onclick=toggle;$('#start').onclick=toggle;$('#seek').oninput=e=>{videos[index].currentTime=Number(e.target.value);render()};$('#mute').onclick=()=>{const muted=!videos[index].muted;videos.forEach(v=>v.muted=muted);$('#mute').style.opacity=muted?'.35':'1';$('#mute').setAttribute('aria-label',muted?'Unmute audio':'Mute audio')};$('#fullscreen').onclick=()=>document.fullscreenElement?document.exitFullscreen():$('.film').requestFullscreen?.();
$('#previous').onclick=$('.left-preview').onclick=()=>select(index-1,-1);$('#next').onclick=$('.right-preview').onclick=()=>select(index+1,1);
document.addEventListener('keydown',e=>{if(e.target.matches('input'))return;if(e.key==='ArrowRight'){e.preventDefault();select(index+1,1)}if(e.key==='ArrowLeft'){e.preventDefault();select(index-1,-1)}});
let touchStart=null;$('#episode-card').addEventListener('touchstart',e=>{if(!e.target.closest('.playback'))touchStart=e.touches[0].clientX},{passive:true});$('#episode-card').addEventListener('touchend',e=>{if(touchStart!==null){const dx=e.changedTouches[0].clientX-touchStart;if(Math.abs(dx)>70)select(index+(dx<0?1:-1),dx<0?1:-1)}touchStart=null},{passive:true});
function sizePreviews(){const card=$('#episode-card');$('.episode-carousel').style.setProperty('--preview-height',`${Math.round(card.getBoundingClientRect().height*.88)}px`)}
new ResizeObserver(sizePreviews).observe($('#episode-card'));
function notifySize(){if(window.parent!==window)window.parent.postMessage({type:'ivg-demo-height',height:Math.ceil(document.body.getBoundingClientRect().height)},location.origin)}
new ResizeObserver(notifySize).observe(document.body);window.addEventListener('resize',render);select(0);
if('requestVideoFrameCallback' in HTMLVideoElement.prototype){videos.forEach((v,i)=>{const frame=()=>{if(index===i)render();v.requestVideoFrameCallback(frame)};v.requestVideoFrameCallback(frame)})}else{const frame=()=>{if(!videos[index].paused)render();requestAnimationFrame(frame)};requestAnimationFrame(frame)}
