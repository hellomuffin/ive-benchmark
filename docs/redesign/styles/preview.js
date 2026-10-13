(() => {
  const originalNames = {atelier: 'Blue Atelier', folio: 'Research Folio', notebook: 'Lilac Notebook'};
  const launchNames = {frontier:'Visual Launch', precision:'Precision', editorial:'Editorial'};
  const theme = new URLSearchParams(location.search).get('style');
  const isLaunch = Boolean(launchNames[theme]);
  const names = theme==='meta' ? {meta:'Meta-inspired study'} : isLaunch ? launchNames : originalNames;
  if (!names[theme]) return;
  document.documentElement.dataset.style = theme;
  const sheet = document.createElement('link');
  sheet.rel = 'stylesheet';
  sheet.href = 'styles/themes.css';
  document.head.append(sheet);
  if(theme==='meta'){
    const metaSheet=document.createElement('link');metaSheet.rel='stylesheet';metaSheet.href='styles/meta.css';document.head.append(metaSheet);
  }
  if (isLaunch) {
    const launchSheet = document.createElement('link');
    launchSheet.rel='stylesheet'; launchSheet.href='styles/launch.css';
    document.head.append(launchSheet);
  }
  document.addEventListener('DOMContentLoaded', () => {
    const bar = document.createElement('aside');
    bar.className = 'style-switcher';
    bar.setAttribute('aria-label', 'Design preview');
    bar.innerHTML = `<a href="styles/${isLaunch?'launch/':''}">All designs</a><span class="style-options">${Object.entries(names).map(([key,name]) => `<a href="?style=${key}${location.hash}" ${key===theme?'aria-current="page"':''}>${name}</a>`).join('')}</span><a href="./">Original</a>`;
    document.body.prepend(bar);
    if(theme==='meta'){
      document.querySelector('.title-name').innerHTML='<span>Interactive </span><span class="art-title">Visual Gym:</span>';
      const art=document.createElement('div');art.className='launch-art';art.setAttribute('aria-hidden','true');
      art.innerHTML=`<svg viewBox="0 0 620 600" fill="none" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="thread-color" x1="90" y1="50" x2="500" y2="580" gradientUnits="userSpaceOnUse"><stop stop-color="#bad5ef"/><stop offset=".42" stop-color="#3178bd"/><stop offset=".73" stop-color="#80b1d0"/><stop offset="1" stop-color="#d7e5ed"/></linearGradient><radialGradient id="thread-light"><stop stop-color="#c9e3f4" stop-opacity=".7"/><stop offset="1" stop-color="#edf5f7" stop-opacity="0"/></radialGradient></defs><ellipse cx="330" cy="300" rx="280" ry="265" fill="url(#thread-light)"/><g stroke="url(#thread-color)" stroke-width="1.1">${Array.from({length:24},(_,i)=>{const d=i*5;return `<path d="M ${110+d*.6} ${550-d*.22} C ${-70+d} ${355-d*.1}, ${210+d*.48} ${-40+d*.3}, ${399+d*.38} ${105+d*.45} C ${655-d*.4} ${300+d*.4}, ${130+d*.1} ${566-d*.35}, ${148+d*.4} ${271+d*.5} C ${163+d*.4} ${81+d*.6}, ${510-d*.2} ${102+d*.3}, ${533-d*.25} ${398+d*.38}"/>`}).join('')}</g><g class="art-sparks" fill="#438ac3"><circle cx="346" cy="151" r="3"/><circle cx="208" cy="379" r="4"/><circle cx="497" cy="339" r="3"/></g></svg>`;
      document.querySelector('.publication-header').append(art);
      document.querySelectorAll('#environment-simulation,#user-simulation').forEach(section=>{
        const intro=document.createElement('div');intro.className='chapter-opening';
        const heading=section.querySelector('.technical-subtitle');const prose=heading.nextElementSibling;
        section.prepend(intro);intro.append(heading,document.createTextNode('\n'),prose);
      });
    }
    if(isLaunch){
      const toc=document.createElement('nav');toc.className='chapter-nav';toc.setAttribute('aria-label','Technical details subsections');
      document.querySelectorAll('.technical-details>.technical-section').forEach(section=>{const a=document.createElement('a');a.href='#'+section.id;a.textContent=section.querySelector('h3').textContent;toc.append(a)});
      document.querySelector('.technical-introduction').append(toc);
    }
    const headings = document.querySelectorAll('.technical-details .technical-subtitle');
    headings.forEach((heading, i) => {
      const index = document.createElement('span');
      index.className = 'chapter-index';
      index.setAttribute('aria-hidden', 'true');
      index.textContent = String(i + 1).padStart(2, '0');
      heading.prepend(index);
    });
  });
})();
