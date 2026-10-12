const video=document.querySelector('#source'), play=document.querySelector('#play'), seek=document.querySelector('#seek');
const topCtx=document.querySelector('#top').getContext('2d'), egoCtx=document.querySelector('#ego').getContext('2d');
let mode='balanced';
const descriptions={balanced:'Equal space for the kitchen and the user’s view; dialogue follows beneath.',focus:'The user’s observation leads; a smaller top-down view preserves spatial context.',dialogue:'The exchange stays beside both observations, keeping more conversational context visible.'};
document.querySelectorAll('nav button').forEach(button=>button.addEventListener('click',()=>{mode=button.dataset.mode;document.querySelector('#demo').className='demo '+mode;document.querySelector('#description').textContent=descriptions[mode];document.querySelectorAll('nav button').forEach(b=>{b.classList.toggle('selected',b===button);b.setAttribute('aria-pressed',b===button)});render();}));
play.addEventListener('click',async()=>{if(video.paused){if(video.ended)video.currentTime=0;try{await video.play()}catch(e){play.textContent='Try play'}}else video.pause()});
video.addEventListener('play',()=>play.textContent='Ⅱ Pause');video.addEventListener('pause',()=>play.textContent=video.ended?'↻ Replay':'▶ Play');video.addEventListener('ended',()=>play.textContent='↻ Replay');
seek.addEventListener('input',()=>{video.currentTime=Number(seek.value);render()});
document.querySelector('#sound').addEventListener('click',e=>{video.muted=!video.muted;e.target.textContent=video.muted?'Sound off':'Sound on';e.target.setAttribute('aria-label',video.muted?'Unmute audio':'Mute audio')});
function render(){
 if(video.readyState>=2){topCtx.drawImage(video,0,34,640,480,0,0,640,480);egoCtx.drawImage(video,642,34,640,480,0,0,640,480)}
 const t=video.currentTime+19.8; const tick=DATA.segments.filter(s=>s.start<=t+.001).at(-1)?.tick??33;
 document.querySelector('#tick').textContent='Tick '+tick;
 const progress=DATA.states.find(s=>s.tick===tick)?.progress??.55;
 document.querySelector('#rice-progress').style.width=100*progress+'%';
 document.querySelector('#task-status').textContent=tick>=42?'Rice cooked · ready to collect':'Rice is cooking';
 document.querySelector('#event-status').textContent=tick>=42?'Omission: skip the tortilla':'Request: notify when rice is ready';
 document.querySelector('#event-detail').textContent=tick>=42?'Scheduled deviation activated at tick 42':'User request active since tick 23';
 const lines=DATA.dialogue.filter(d=>d.start<=t).slice(mode==='dialogue'?-4:-2);
 const container=document.querySelector('#lines');container.replaceChildren();
 if(!lines.length){const p=document.createElement('div');p.className='line user';p.innerHTML='<span class="speaker">User · t23</span><span>Give me a shout the moment the rice is done, would you?</span>';container.append(p)}
 lines.forEach((d,i)=>{const row=document.createElement('div');row.className='line '+d.speaker+(i<lines.length-1?' old':'');const label=document.createElement('span');label.className='speaker';label.textContent=(d.speaker==='user'?'User':'Assistant')+' · t'+d.tick;const sentence=document.createElement('span');const words=d.text.split(/\s+/);words.forEach((w,j)=>{const span=document.createElement('span');span.className='word'+(t>=d.start+(d.words[j]?.start??0)?' spoken':'');span.textContent=w+' ';sentence.append(span)});row.append(label,sentence);container.append(row)});
 seek.value=video.currentTime;document.querySelector('#time').textContent='0:'+String(Math.floor(video.currentTime)).padStart(2,'0')+' / 0:16';
}
video.addEventListener('loadeddata',render);video.addEventListener('seeked',render);
function loop(){if(!video.paused)render();requestAnimationFrame(loop)}loop();render();
