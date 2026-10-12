const $=s=>document.querySelector(s), video=$('#source');
const contexts=[$('#world').getContext('2d'),$('#ego').getContext('2d')];
const iconPaths=[
 '<path d="M4 12H28C27 23 23 27 16 27S5 23 4 12Z" fill="currentColor"/><path d="M8 9Q10 4 12 9M14 8Q16 2 18 8M21 9Q23 4 25 9" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
 '<path d="M6 8C14 0 22 6 27 13S21 29 13 27S0 17 6 8Z" fill="currentColor"/><path d="M9 10C14 6 22 10 22 16S15 24 10 20S5 14 9 10Z" fill="none" stroke="white" stroke-width="1.5"/><circle cx="17" cy="13" r="2" fill="white"/>',
 '<path d="M16 10C4 3 0 21 9 27C14 31 26 28 28 19C30 9 22 5 16 10Z" fill="currentColor"/><path d="M16 12L10 5L16 7L19 2L20 8L25 7Z" fill="currentColor" stroke="#edf6fd" stroke-width="1"/>',
 '<path d="M16 29C4 26 0 19 6 14C-1 7 9 0 15 6C22-3 33 7 26 14C35 21 26 29 16 29Z" fill="currentColor"/><path d="M16 28V10M16 21L9 15M16 18L23 10" stroke="#edf6fd" stroke-width="1.4" fill="none"/>',
 '<ellipse cx="16" cy="19" rx="14" ry="8" fill="none" stroke="currentColor" stroke-width="2"/><ellipse cx="16" cy="19" rx="9" ry="4" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M10 6H22L25 13H7Z" fill="currentColor"/>',
 '<path d="M3 23H29M5 20C5 7 27 7 27 20ZM16 8V5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><circle cx="16" cy="4" r="2" fill="currentColor"/>'
];
const labels=['Start rice','Rice cooked','Cook steak','Chop tomato','Chop lettuce','Assemble','Serve'];
const events=['<div class="event request" title="Request: notify when the rice is ready"><span class="event-dot">?</span><span>Rice-ready alert</span></div>','<div class="event omission"><span class="event-dot">!</span><span>Skip tortilla</span></div>'];
$('#milestones').innerHTML=labels.map((l,i)=>`<div class="milestone ${i===0?'done started-step':i===1?'active rice-step':''}"><div class="food"><svg viewBox="0 0 32 32" aria-hidden="true">${iconPaths[Math.max(0,i-1)]}</svg></div><span>${l}</span>${events[i]??''}</div>`).join('');
document.querySelectorAll('[data-layout]').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('[data-layout]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));$('#composition').className=b.dataset.layout;history.replaceState(null,'','#'+b.dataset.layout);render()}));
let started=false, lastTick=-1, previous={assistant:'',user:''}, currentCues={assistant:null,user:null};
const playIcon='<svg viewBox="0 0 24 24"><path d="M8 4L20 12L8 20Z"/></svg>',pauseIcon='<svg viewBox="0 0 24 24"><path d="M6 4H10V20H6ZM14 4H18V20H14Z"/></svg>';
async function toggle(){if(video.paused){if(video.ended)video.currentTime=0;try{await video.play();started=true;$('.film').classList.add('started')}catch(e){$('#play').setAttribute('aria-label','Retry playback')}}else video.pause()}
$('#start').onclick=toggle;$('#play').onclick=toggle;
video.onplay=()=>{$('#play').innerHTML=pauseIcon;$('#play').setAttribute('aria-label','Pause video')};video.onpause=()=>{$('#play').innerHTML=playIcon;$('#play').setAttribute('aria-label',video.ended?'Replay video':'Play video');document.querySelectorAll('.is-speaking').forEach(e=>e.classList.remove('is-speaking'))};
$('#mute').onclick=()=>{video.muted=!video.muted;$('#mute').style.opacity=video.muted?'.4':'1';$('#mute').setAttribute('aria-label',video.muted?'Unmute audio':'Mute audio')};
$('#fullscreen').onclick=()=>{if(document.fullscreenElement)document.exitFullscreen();else $('.film').requestFullscreen?.()};
$('#seek').oninput=e=>{video.currentTime=Number(e.target.value);render()};
function speech(speaker,t){
 const d=EPISODE.dialogue.filter(d=>d.speaker===speaker&&d.start<=t).at(-1);
 const fallback=speaker==='user'?'Give me a shout the moment the rice is done, would you?':'';
 const text=d?.text??fallback,node=$('#'+speaker+'-line'),block=$('.'+speaker+'-speech');
 node.classList.toggle('empty',!text);
 const latest=EPISODE.dialogue.filter(d=>d.start<=t).at(-1);
 block.classList.toggle('past',!!latest&&latest.speaker!==speaker);
 if(previous[speaker]!==text){previous[speaker]=text;block.classList.remove('changed');node.replaceChildren();text.split(/\s+/).forEach((word,i)=>{const span=document.createElement('span');span.textContent=word+(i<text.split(/\s+/).length-1?' ':'');node.append(span)});void block.offsetWidth;block.classList.add('changed')}
 [...node.children].forEach((word,i)=>word.classList.toggle('future',!!d&&t<d.start+(d.words[i]?.start??0)));
 block.classList.toggle('is-speaking',!video.paused&&!!d&&t>=d.start&&t<d.start+d.duration);
}
function render(){
 if(video.readyState>=2){contexts[0].drawImage(video,0,34,640,480,0,0,640,480);contexts[1].drawImage(video,642,34,640,480,0,0,640,480)}
 const time=video.currentTime,t=time+19.8,tick=EPISODE.segments.filter(s=>s.start<=t+.001).at(-1)?.tick??33;
 if(tick!==lastTick){lastTick=tick;const progress=EPISODE.rice.find(x=>x.tick===tick)?.progress??.55;$('.rice-step .food').style.setProperty('--cook',progress);$('.rice-step').classList.toggle('done',tick>=42);$('.omission').classList.toggle('triggered',tick>=42);$('#rice-marker').classList.toggle('ready',tick>=42);$('.rice-step').setAttribute('aria-label',tick>=42?'Rice cooked':'Rice cooking');$('.omission').setAttribute('aria-label',tick>=42?'Skip tortilla event triggered when rice is cooked':'Skip tortilla event scheduled when rice is cooked')}
 speech('assistant',t);speech('user',t);$('#seek').value=time;$('#timestamp').textContent='0:'+String(Math.floor(time)).padStart(2,'0')+' / 0:16';
}
video.addEventListener('loadeddata',render);video.addEventListener('seeked',render);video.addEventListener('ended',render);
function frame(){if(!video.paused)render();requestAnimationFrame(frame)}requestAnimationFrame(frame);render();
if(location.hash==='#cinema')document.querySelector('[data-layout="cinema"]').click();
