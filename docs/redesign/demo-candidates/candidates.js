const data=await fetch('candidates.json').then(r=>r.json());
const host=document.querySelector('#candidate'),tabs=document.querySelector('.candidate-tabs');
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
tabs.innerHTML=data.candidates.map((c,i)=>`<button role="tab" data-index="${i}" aria-selected="${i===0}"><b>${c.letter}</b>${c.engine}</button>`).join('');
const turn=(x,i)=>`<div class="turn ${x.who==='human'?'human':''}" data-turn="${i}"><div class="turn-meta"><b>${x.who==='human'?'User':'Model'}</b><span>Tick ${x.t}</span></div><p>${esc(x.text)}</p></div>`;
function show(i){
 const c=data.candidates[i];
 tabs.querySelectorAll('button').forEach(b=>b.setAttribute('aria-selected',String(+b.dataset.index===i)));
 const prior=host.querySelector('video');if(prior)prior.pause();
 host.innerHTML=`<article class="candidate-card"><div class="candidate-heading"><h2>${c.title}</h2><p class="task">${c.task}</p><div class="identity"><span><b>Model</b> ${c.modelLabel}</span><span><b>User</b> ${c.personaLabel}</span></div></div><div class="candidate-body ${c.id==='screensim'?'screen-layout':''}"><div><div class="preview ${c.id==='screensim'?'screen':''}">${c.id==='screensim'?'':`<div class="views">${c.id==='cooksim'?'<span>Top-down</span><span>Egocentric</span>':'<span>Egocentric</span><span>Top-down</span>'}</div>`}<video controls playsinline preload="metadata" poster="${c.poster}" src="${c.video}" aria-label="${c.engine} candidate excerpt"></video></div><div class="outcome"><div><span>Full-episode outcome</span><strong class="${c.outcome.includes('late')?'late':''}">${c.outcome}</strong><small>${c.ticks} ticks${c.budget?` · budget ${c.budget}`:''}</small>${c.reference?`<small>Reference execution: ${c.reference} ticks</small>`:''}</div><div><span>Interaction quality</span><strong>${c.quality.toFixed(1)}%</strong><div class="quality-track"><i style="width:${c.quality}%"></i></div></div></div><div class="moments">${c.moments.map(m=>`<button data-tick="${m.t}">t=${m.t} · ${m.text}</button>`).join('')}</div></div><div><p class="dialogue-title">Recorded dialogue · ${c.id==='screensim'?'full episode':`excerpt, ticks ${c.startTick}–${c.endTick}`}</p><div class="dialogue excerpt">${c.excerptDialogue.map(turn).join('')}</div></div></div><div class="rationale"><h3>Why this episode</h3><p>${c.reason}</p><div class="event-tags">${c.events.map(e=>`<span>${e}</span>`).join('')}</div></div><details class="record-details"><summary>Full dialogue and source record</summary><dl><dt>Episode</dt><dd>${esc(c.recordKey.episode)}</dd><dt>Persona</dt><dd>${esc(c.recordKey.persona)}</dd><dt>Run</dt><dd>${c.run} · ${c.timing}</dd><dt>Source</dt><dd class="source-id">${esc(c.source)}</dd></dl><div class="dialogue">${c.dialogue.map(turn).join('')}</div><p><a href="candidates.json" download>Download candidate details</a></p></details></article>`;
 const video=host.querySelector('video');
 function second(t){if(c.id!=='screensim')return Math.max(0,t-c.startTick);return c.cues.find(x=>x.t>=t)?.s??0;}
 host.querySelectorAll('[data-tick]').forEach(b=>b.onclick=()=>{video.currentTime=second(+b.dataset.tick);video.play().catch(()=>{});});
 video.ontimeupdate=()=>{
  const eligible=c.excerptDialogue.map((x,j)=>({j,s:c.id==='screensim'?(c.cues.find(y=>y.t===x.t&&y.text===x.text)?.s??second(x.t)):second(x.t)})).filter(x=>x.s<=video.currentTime);
  const active=eligible.length?eligible[eligible.length-1].j:-1;
  host.querySelectorAll('.excerpt .turn').forEach((el,j)=>el.classList.toggle('active',j===active));
 };
}
tabs.querySelectorAll('button').forEach(b=>b.onclick=()=>show(+b.dataset.index));show(0);
