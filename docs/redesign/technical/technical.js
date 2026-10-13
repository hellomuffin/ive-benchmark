const media = new URL('./media/', import.meta.url);
const asset = (name, ext = 'mp4') => new URL(`${name}.${ext}`, media).href;
const tasks = [
  {id:'task-cook', engine:'cook', name:'Prepare a cheeseburger', short:'Cheeseburger', description:'Prepare and serve a cheeseburger, assembling the ingredients in the required order.', goals:['Bun','Fried patty','Cheese'], note:'Reference completion · 3× speed'},
  {id:'task-aftermeal', engine:'vh', name:'Clear up after a meal', short:'After-meal cleanup', description:'Move the used dishes into the dishwasher and return the apple to the fridge.', goals:['Collect two plates and a mug','Load the dishwasher','Put away the apple; close both appliances'], note:'Task completion'},
  {id:'task-guest', engine:'vh', name:'Prepare for a guest', short:'Prepare for a guest', description:'Clear the living room: put away dishes, return the pillow, and turn off the TV.', goals:['Put the plate and mug in the dishwasher','Return the pillow to the bed','Switch off the TV'], note:'Task completion'},
  {id:'task-bedroom', engine:'vh', name:'Tidy the bedroom', short:'Tidy the bedroom', description:'Restore the bedroom and take the used mug to the kitchen.', goals:['Return the book to the desk','Turn off the lamp and close the cabinet','Take the mug to the kitchen table'], note:'Task completion'},
  {id:'task-phone', engine:'screen', name:'Restrict an app’s access', short:'App privacy', description:'Restrict TripSnap’s access without changing permissions for other apps.', goals:['Disable location access','Disable cross-app tracking','Disable background refresh'], note:'Task completion'},
];
const names = {cook:'CookSim',vh:'VHSim',screen:'ScreenSim'};
let taskIndex=0;
const video=document.querySelector('#task-video');
let phoneFocus=[];
fetch(new URL('./phone-focus.json',import.meta.url)).then(r=>r.json()).then(data=>{phoneFocus=data;drawFocus()});
const focusCanvas=document.querySelector('#phone-focus'),focusContext=focusCanvas.getContext('2d');
function drawFocus(){
 if(tasks[taskIndex].engine!=='screen'||video.readyState<2)return;
 const segment=phoneFocus.find(s=>video.currentTime>=s.start&&video.currentTime<s.end)||phoneFocus[phoneFocus.length-1];
 const y=segment?segment.y:0;
 focusContext.drawImage(video,0,y,video.videoWidth,video.videoHeight/2,0,0,focusCanvas.width,focusCanvas.height);
}
video.addEventListener('loadeddata',drawFocus);video.addEventListener('seeked',drawFocus);video.addEventListener('timeupdate',drawFocus);
if('requestVideoFrameCallback' in video){const frame=()=>{drawFocus();video.requestVideoFrameCallback(frame)};video.requestVideoFrameCallback(frame);}
const thumbs=document.querySelector('#task-thumbnails');
for(const [i,task] of tasks.entries()){
  const b=document.createElement('button');b.type='button';b.className='task-thumb';b.setAttribute('aria-label',`${names[task.engine]}: ${task.name}`);
  b.innerHTML=`<img src="${asset(task.id,'jpg')}" alt="" loading="lazy"><span>${task.short}<small>${names[task.engine]}</small></span>`;
  b.addEventListener('click',()=>setTask(i));thumbs.append(b);
}
function setTask(i){
  taskIndex=(i+tasks.length)%tasks.length;const t=tasks[taskIndex];video.pause();video.poster=asset(t.id,'jpg');video.src=asset(t.id);video.load();video.setAttribute('aria-label',`${names[t.engine]}: ${t.name} — ${t.note}`);
  document.querySelector('.task-stage').dataset.engine=t.engine;
  document.querySelector('#task-name').textContent=t.name;
  document.querySelector('#task-description').textContent=t.description;
  document.querySelector('#task-goals').replaceChildren(...t.goals.map(g=>{const e=document.createElement('li');e.textContent=g;return e}));
  document.querySelector('#task-counter').textContent=`${taskIndex+1} / ${tasks.length}${t.engine==='cook'?' · 3×':''}`;
  document.querySelectorAll('[data-engine]').forEach(b=>{if(b.tagName==='BUTTON')b.setAttribute('aria-pressed',b.dataset.engine===t.engine)});
  [...thumbs.children].forEach((b,j)=>b.setAttribute('aria-pressed',j===taskIndex));
  const selected=thumbs.children[taskIndex];thumbs.scrollTo({left:Math.max(0,selected.offsetLeft-thumbs.offsetLeft-thumbs.clientWidth/2+selected.offsetWidth/2),behavior:reduced?'instant':'smooth'});
}
const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
document.querySelectorAll('.engine-tabs button').forEach(b=>b.addEventListener('click',()=>setTask(tasks.findIndex(t=>t.engine===b.dataset.engine))));
document.querySelector('#task-prev').addEventListener('click',()=>setTask(taskIndex-1));
document.querySelector('#task-next').addEventListener('click',()=>setTask(taskIndex+1));
setTask(0);
const observer=new IntersectionObserver(entries=>entries.forEach(({target,intersectionRatio})=>{
  if(intersectionRatio>.3&&!reduced&&target.dataset.paused!=='true'){target.play().catch(()=>{});}else target.pause();
}),{threshold:[0,.3]});
function miniFilm(id,label){
  const box=document.createElement('div');box.className='mini-film';
  const v=document.createElement('video');v.muted=true;v.loop=true;v.playsInline=true;v.preload='none';v.poster=asset(id,'jpg');v.src=asset(id);v.setAttribute('aria-label',label);
  const b=document.createElement('button');b.type='button';b.className='motion-toggle';b.textContent='▶';b.setAttribute('aria-label',`Play ${label}`);
  b.addEventListener('click',()=>{if(v.paused){v.dataset.paused='false';v.play().catch(()=>{});}else{v.dataset.paused='true';v.pause();}});
  v.addEventListener('play',()=>{b.textContent='Ⅱ';b.setAttribute('aria-label',`Pause ${label}`)});
  v.addEventListener('pause',()=>{b.textContent='▶';b.setAttribute('aria-label',`Play ${label}`)});
  box.append(v,b);observer.observe(v);return box;
}
const actions=[['action-pan','Go to the pan with the meat','CookSim'],['action-rice','Pick up rice from a cooked pot','CookSim'],['action-fridge','Go to the fridge on the left','VHSim'],['action-book','Put the book on the nearest coffee table','VHSim']];
for(const [id,label,engine] of actions){const f=document.createElement('figure');f.className='action-example';f.append(miniFilm(id,label));const cap=document.createElement('figcaption');cap.textContent=label;const small=document.createElement('small');small.textContent=engine;cap.append(small);f.append(cap);document.querySelector('#action-examples').append(f);}
const events=[
 ['event-extra','Execution error','Extra ingredient','Add an ingredient not required by the recipe.'],
 ['event-raw','Execution error','Serve raw food','Plate an ingredient without cooking it.'],
 ['event-unattended','Execution error','Unattended cooking','Leave food on the heat for too long.'],
 ['event-plan','Plan change','Change the plan','Announce a different next step.'],
 ['event-question','Question','Ask a question','Ask about the ongoing task.'],
];
for(const [id,type,title,description] of events){const f=document.createElement('figure');f.className='event-example';f.append(miniFilm(id,title));const cap=document.createElement('figcaption');const tag=document.createElement('span');tag.className='event-type';tag.textContent=type;const h=document.createElement('h4');h.textContent=title;const p=document.createElement('p');p.textContent=description;cap.append(tag,h,p);f.append(cap);document.querySelector('#event-examples').append(f);}
const axes=[
 {key:'skill',title:'Skill level',levels:['Low','Medium','High']},
 {key:'trust',title:'Trust in AI',levels:['Low','Medium','High']},
 {key:'speed',title:'Execution speed',levels:['Cautious','Balanced','Quick']},
 {key:'interruption',title:'Interruption preference',levels:['Step-by-step','Moderate','Necessary only']},
];
const excerpts={
 skill:['You are new to this kind of kitchen work, and the routines still take effort to picture.','You are comfortable with ordinary kitchen tasks and can usually translate a cooking goal into practical steps.','You are very experienced in the kitchen and tend to keep the whole workflow in mind. You naturally think ahead about timing, dependencies, tools, and likely failure points, and you can explain those considerations in concrete cooking terms.'],
 trust:["You are cautious about the assistant's claims about what happened in your work, especially when they do not match your own memory. Your first instinct in that mismatch is to question what it actually saw and compare the claim with the state of the kitchen before changing course.","You treat the assistant as potentially helpful but not automatically right. If its account conflicts with yours, you tend to look for a sensible reason before revising your view.","You generally regard the assistant as a useful extra set of eyes and are inclined to take its observations seriously."],
 speed:['You strongly prefer a methodical, cautious approach to cooking, believing that a slow, correct dish is better than a rushed, ruined one.','You prefer a balanced pace. You like steady progress and are comfortable with some efficiency, but not at the cost of making the work feel rushed or brittle.','You are driven by efficiency and want to complete the dish as quickly as possible. You are drawn to momentum, overlap, and avoiding wasted pauses when the situation seems manageable.'],
 interruption:['You prefer close guidance as the task unfolds. You are comfortable having the assistant break things down and keep you oriented, because frequent direction reduces uncertainty.','You prefer a middle-ground interruption style. You can absorb comments while working, but you also appreciate some respect for the rhythm of the task.','You prefer not to be interrupted unless there is a real need. Extra commentary during active work can feel intrusive, especially if it is not urgent or directly useful.'],
};
function instruction(axis,level){document.querySelector('#persona-instruction-title').textContent=`${axis.title} · ${axis.levels[level]}`;document.querySelector('#persona-instruction-text').textContent=excerpts[axis.key][level];}
for(const axis of axes){
 const row=document.createElement('fieldset');row.className='persona-row';const title=document.createElement('legend');title.textContent=axis.title;const choices=document.createElement('div');choices.className='persona-levels';
 axis.levels.forEach((label,i)=>{const b=document.createElement('button');b.type='button';b.textContent=label;b.setAttribute('aria-pressed',i===(axis.key==='interruption'?2:1));b.addEventListener('click',()=>{[...choices.children].forEach((s,j)=>s.setAttribute('aria-pressed',i===j));instruction(axis,i);});choices.append(b);});
 row.append(title,choices);document.querySelector('#persona-controls').append(row);
}
instruction(axes[3],2);
document.addEventListener('visibilitychange',()=>{if(document.hidden)document.querySelectorAll('.technical-section video').forEach(v=>v.pause());});
new IntersectionObserver(entries=>entries.forEach(e=>{if(!e.isIntersecting)e.target.pause();}),{threshold:0}).observe(video);
