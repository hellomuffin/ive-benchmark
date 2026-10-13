(() => {
  const originalNames = {atelier: 'Blue Atelier', folio: 'Research Folio', notebook: 'Lilac Notebook'};
  const launchNames = {frontier:'Visual Launch', precision:'Precision', editorial:'Editorial'};
  const theme = new URLSearchParams(location.search).get('style');
  const isLaunch = Boolean(launchNames[theme]);
  const names = isLaunch ? launchNames : originalNames;
  if (!names[theme]) return;
  document.documentElement.dataset.style = theme;
  const sheet = document.createElement('link');
  sheet.rel = 'stylesheet';
  sheet.href = 'styles/themes.css';
  document.head.append(sheet);
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
    if(isLaunch){
      const toc=document.createElement('nav');toc.className='chapter-nav';toc.setAttribute('aria-label','Technical details subsections');
      document.querySelectorAll('.technical-details>.technical-section').forEach(section=>{const a=document.createElement('a');a.href='#'+section.id;a.textContent=section.querySelector('h3').textContent;toc.append(a)});
      document.querySelector('.technical-introduction').append(toc);
    }
    const headings = document.querySelectorAll('.technical-details > .technical-section > .technical-subtitle');
    headings.forEach((heading, i) => {
      const index = document.createElement('span');
      index.className = 'chapter-index';
      index.setAttribute('aria-hidden', 'true');
      index.textContent = String(i + 1).padStart(2, '0');
      heading.prepend(index);
    });
  });
})();
