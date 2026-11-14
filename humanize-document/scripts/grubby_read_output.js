// Read Grubby's output from the humanizer page after Humanize was clicked.
// The output panel has three view tabs: Humanized (default), Polished and Detection.
// Set window.__TAB = 'Polished' (or 'Humanized') to switch the view first; switching
// only changes what the panel shows, it sends nothing and costs nothing.
// The tool result is cut off around 1,000 characters, so the full text is kept in
// window.__O and returned in slices: run again with window.__S = 900, 1800, ... for more.
const want = window.__TAB || 'Humanized';
const selected = () => ([...document.querySelectorAll('[role=tab]')]
  .find(t => t.getAttribute('aria-selected') === 'true') || {}).innerText?.trim();
if (selected() !== want) {
  const tab = [...document.querySelectorAll('[role=tab]')].find(t => t.innerText.trim() === want);
  if (tab) { tab.click(); await new Promise(r => setTimeout(r, 600)); }
}
const page = document.body.innerText;
// The output text sits after the "Humanize" button and before the "Output" word count.
const start = page.indexOf('Humanize\n', page.indexOf('ZeroGPT'));
const end = page.indexOf('\nOutput\n', start);
if (start < 0 || end < start) {
  'NO OUTPUT YET. Page tail: ' + page.slice(-300);
} else {
  window.__O = page.slice(start + 'Humanize\n'.length, end).trim();
  const norm = s => s.replace(/\s+/g, ' ').trim();
  const input = document.querySelector('.ProseMirror')?.innerText || '';
  const sameAsInput = norm(window.__O) === norm(input);
  const from = window.__S || 0;
  `view=${selected()} | sameAsInput=${sameAsInput} | ${window.__O.length} chars | from ${from} | `
    + window.__O.slice(from, from + 900);
}
