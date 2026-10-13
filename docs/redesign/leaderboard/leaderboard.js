const host=document.querySelector('#leaderboard');
const dataURL=new URL('../../data/leaderboard.json',import.meta.url);
const data=await fetch(dataURL).then(r=>r.json());
const families=[{key:'Frontier API',label:'API · Non-streaming',color:'#397cac'},{key:'Streaming API',label:'API · Streaming',color:'#67acc8'},{key:'Open non-streaming',label:'Open · Non-streaming',color:'#b99a55'},{key:'Open streaming',label:'Open · Streaming',color:'#bc704e'}];
let environment='overall',sort='success',selection=null,familyFilter=null,xMax=60,yMax=80;
const modelNames={'Kimi-VL-A3B-Thinking':'Kimi-VL-Thinking'};
const safe=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('"','&quot;');
const values=m=>environment==='overall'?m.overall:m.engines[environment];
const color=m=>families.find(f=>f.key===m.family).color;
host.className='lb';
host.innerHTML=`<div class="lb-toolbar"><div class="lb-tabs" role="tablist" aria-label="Leaderboard environment">${[['overall','Overall'],['cooksim','CookSim'],['vhhome','VHSim'],['screensim','ScreenSim']].map(([k,n])=>`<button role="tab" data-env="${k}" aria-selected="${k===environment}">${n}</button>`).join('')}</div></div><div class="lb-layout"><div class="lb-plot"><div class="lb-plot-heading">Task success × interaction quality</div><svg class="lb-chart" viewBox="0 0 500 415" aria-label="Task success versus interaction quality"></svg><div class="lb-tooltip" hidden></div><div class="lb-legend">${families.map(f=>`<button data-family="${f.key}" aria-pressed="false" style="--family:${f.color}"><i></i>${f.label}</button>`).join('')}</div><div class="lb-selection"></div></div><div class="lb-table-wrap"><table><colgroup><col><col><col><col></colgroup><thead><tr><th>Assistant</th><th><button data-sort="success">In-time<br>success (%)</button></th><th><button data-sort="quality">Interaction<br>quality (%)</button></th><th><button data-sort="recall">Detection<br>recall (%)</button></th></tr></thead><tbody></tbody></table></div></div><div class="lb-footer"><a href="${dataURL.href}" download="ivg-bench-leaderboard.json">Results data ↓</a></div>`;
const $=s=>host.querySelector(s);let ordered=[];
function render(){
 ordered=families.flatMap(f=>data.models.filter(m=>m.family===f.key).sort((a,b)=>values(b)[sort]-values(a)[sort]));
 host.querySelectorAll('[data-env]').forEach(b=>b.setAttribute('aria-selected',String(b.dataset.env===environment)));
 host.querySelectorAll('[data-sort]').forEach(b=>{b.classList.toggle('sorting',b.dataset.sort===sort);b.parentElement.setAttribute('aria-sort',b.dataset.sort===sort?'descending':'none')});
 const max=Object.fromEntries(['success','quality','recall'].map(k=>[k,Math.max(...ordered.map(m=>values(m)[k]??-1))]));
 $('tbody').innerHTML=families.map(f=>`<tr class="family-row"><th colspan="4" style="--family:${f.color}"><i></i>${f.label}</th></tr>`+ordered.filter(m=>m.family===f.key).map(m=>{const i=ordered.indexOf(m),v=values(m);return `<tr class="model-row" data-model="${i}" tabindex="0" style="--family:${f.color}" aria-label="${safe(m.model)}, success ${v.success.toFixed(1)}, quality ${v.quality.toFixed(1)}"><td><span class="model-name"><span class="model-number">${i+1}</span>${modelNames[m.model]??m.model}</span></td>${['success','quality','recall'].map(k=>`<td><span class="cell-value ${v[k]===max[k]?'best':''}" style="--score:${v[k]??0}">${v[k]==null?'—':v[k].toFixed(1)}</span></td>`).join('')}</tr>`}).join('')).join('');
 const W=500,H=415,L=54,R=21,T=20,B=54,PW=W-L-R,PH=H-T-B;
 xMax=Math.min(100,Math.ceil((Math.max(...ordered.map(m=>values(m).success))+5)/20)*20);
 yMax=Math.min(100,Math.ceil((Math.max(...ordered.map(m=>values(m).quality))+5)/20)*20);
 const x=v=>L+v/xMax*PW,y=v=>T+(yMax-v)/yMax*PH;
 let svg=`<rect class="plot-frame" x="${L}" y="${T}" width="${PW}" height="${PH}" rx="2"/>`;
 for(let n=0;n<=xMax;n+=xMax<=40?10:20)svg+=`<line class="grid" x1="${x(n)}" y1="${T}" x2="${x(n)}" y2="${H-B}"/><text class="tick" x="${x(n)}" y="${H-B+20}" text-anchor="middle">${n}</text>`;
 for(let n=0;n<=yMax;n+=20)svg+=`<line class="grid" x1="${L}" y1="${y(n)}" x2="${W-R}" y2="${y(n)}"/><text class="tick" x="${L-12}" y="${y(n)+3}" text-anchor="end">${n}</text>`;
 svg+=`<text class="axis-label" x="${L+PW/2}" y="${H-7}" text-anchor="middle">In-time task success (%)</text><text class="axis-label" transform="translate(15,${T+PH/2}) rotate(-90)" text-anchor="middle">Interaction quality (%)</text><g class="highlights"></g>`;
 const labels=ordered.map(m=>{const v=values(m);return {px:x(v.success),py:y(v.quality),x:x(v.success)+11,y:y(v.quality)-6}});
 for(let pass=0;pass<120;pass++)for(let i=0;i<labels.length;i++){
  const a=labels[i];for(let j=0;j<i;j++){const b=labels[j];if(Math.abs(a.x-b.x)<20&&Math.abs(a.y-b.y)<15){const push=(15-Math.abs(a.y-b.y))/2+.1;if(a.y<=b.y){a.y-=push;b.y+=push}else{a.y+=push;b.y-=push}}}
  for(let j=0;j<labels.length;j++){const b=labels[j];if(j!==i&&Math.abs(a.x-b.px)<13&&Math.abs(a.y-b.py)<11)a.x+=1}
  a.x=Math.max(L+7,Math.min(W-R-12,a.x));a.y=Math.max(T+10,Math.min(H-B-9,a.y));
 }
 svg+=ordered.map((m,i)=>{const v=values(m),p=labels[i],dx=p.x-p.px,dy=p.y-p.py;return `<g class="point" data-model="${i}" tabindex="0" role="button" aria-label="${safe(m.model)}: ${v.success.toFixed(1)}% success, ${v.quality.toFixed(1)}% quality" transform="translate(${p.px},${p.py})">${Math.hypot(dx,dy)>20?`<line x1="0" y1="0" x2="${dx-3}" y2="${dy+1}" stroke="${color(m)}" stroke-width=".7" opacity=".6"/>`:''}<circle r="5.5" fill="${color(m)}"/><text x="${dx}" y="${dy}" style="fill:${color(m)}">${i+1}</text><title>${m.model}</title></g>`}).join('');
 $('.lb-chart').innerHTML=svg;
 host.querySelectorAll('[data-model]').forEach(el=>{el.onmouseenter=()=>highlight(Number(el.dataset.model));el.onmouseleave=()=>highlight(selection);el.onfocus=()=>highlight(Number(el.dataset.model));el.onblur=()=>highlight(selection);el.onclick=()=>{const i=Number(el.dataset.model);selection=selection===i?null:i;highlight(selection)};el.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();el.click()}}});
 highlight(selection);
}
function highlight(i){
 const m=i===null?null:ordered[i];
 host.querySelectorAll('[data-model]').forEach(el=>{const j=Number(el.dataset.model);el.classList.toggle('selected',i!==null&&j===i);el.classList.toggle('dimmed',i!==null?j!==i:familyFilter!==null&&ordered[j].family!==familyFilter)});
 host.querySelectorAll('[data-family]').forEach(el=>el.setAttribute('aria-pressed',String(el.dataset.family===familyFilter)));
 const lines=$('.highlights');
 if(m){const v=values(m),x=54+v.success/xMax*425,y=20+(yMax-v.quality)/yMax*341;lines.innerHTML=`<path class="crosshair" d="M54 ${y}H${x}V361"/>`;$('.lb-selection').innerHTML=`<div><strong>${m.model}</strong><p>${families.find(f=>f.key===m.family).label}</p></div><div class="lb-selected-scores"><div><b>${v.success.toFixed(1)}</b><span>Task success</span></div><div><b>${v.quality.toFixed(1)}</b><span>Interaction quality</span></div></div>`}
 else{lines.innerHTML='';$('.lb-selection').innerHTML=''}
}
host.querySelectorAll('[data-env]').forEach(b=>b.onclick=()=>{environment=b.dataset.env;selection=null;render()});
host.querySelectorAll('[data-sort]').forEach(b=>b.onclick=()=>{sort=b.dataset.sort;selection=null;render()});
host.querySelectorAll('[data-family]').forEach(b=>b.onclick=()=>{familyFilter=familyFilter===b.dataset.family?null:b.dataset.family;selection=null;highlight(null)});
render();
