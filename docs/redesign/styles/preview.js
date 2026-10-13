(() => {
  const names = {atelier: 'Blue Atelier', folio: 'Research Folio', notebook: 'Lilac Notebook'};
  const theme = new URLSearchParams(location.search).get('style');
  if (!names[theme]) return;
  document.documentElement.dataset.style = theme;
  const sheet = document.createElement('link');
  sheet.rel = 'stylesheet';
  sheet.href = 'styles/themes.css';
  document.head.append(sheet);
  document.addEventListener('DOMContentLoaded', () => {
    const bar = document.createElement('aside');
    bar.className = 'style-switcher';
    bar.setAttribute('aria-label', 'Design preview');
    bar.innerHTML = `<a href="styles/">All designs</a><span class="style-options">${Object.entries(names).map(([key,name]) => `<a href="?style=${key}${location.hash}" ${key===theme?'aria-current="page"':''}>${name}</a>`).join('')}</span><a href="./">Original</a>`;
    document.body.prepend(bar);
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
