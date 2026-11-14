// After "Detect AI" has finished: JustDone's displayed score, the share of highlighted
// words, and the highlighted share of each paragraph in PREFIXES. Each entry is
// [label, opening words of the paragraph, opening words of the next paragraph]; the
// paragraph spans from the first to the second. Read-only.
const PREFIXES = [
  // ["p1", "Opening words of paragraph", "Opening words of the next paragraph"],
];
const HIGHLIGHTS = ['rgb(250, 240, 199)', 'rgb(235, 173, 36)'];  // flagged, and the selected flag
const isFlagged = el => HIGHLIGHTS.includes(getComputedStyle(el).backgroundColor);
const score = [...document.querySelectorAll('*')]
  .map(e => (e.children.length === 0 ? e.textContent : ''))
  .find(t => /\d+% (Possibly AI|AI|Human)/.test(t));
const spans = [...document.querySelectorAll('span,mark')]
  .filter(e => e.children.length === 0 && e.textContent.length > 20 && isFlagged(e));
let root = spans[0];
while (root && !root.contains(spans[spans.length - 1])) root = root.parentElement;
let full = '';
const marks = [];
if (root) {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  let node;
  while ((node = walker.nextNode())) {
    marks.push([full.length, full.length + node.textContent.length, isFlagged(node.parentElement)]);
    full += node.textContent;
  }
}
const words = s => (s.match(/\S+/g) || []).length;
function share(a, b) {
  if (a < 0 || b <= a) return 'not found';
  let total = 0, flagged = 0;
  for (const [s, e, f] of marks) {
    const lo = Math.max(s, a), hi = Math.min(e, b);
    if (hi > lo) { const n = words(full.slice(lo, hi)); total += n; if (f) flagged += n; }
  }
  return `${flagged}/${total} (${Math.round(100 * flagged / total)}%)`;
}
const result = { score, highlightedPassages: spans.length };
const flaggedWords = marks.filter(m => m[2]).reduce((n, [s, e]) => n + words(full.slice(s, e)), 0);
result.highlightedWords = `${flaggedWords}/${words(full)} (${Math.round(100 * flaggedWords / words(full))}%)`;
for (const [label, a, b] of PREFIXES) result[label] = share(full.indexOf(a), full.indexOf(b));
JSON.stringify(result);
