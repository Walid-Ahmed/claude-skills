// Fill Grubby's humanizer input (a ProseMirror editor) with a batch of paragraphs.
// Before running: click the "Academic (Turnitin)" mode button, then replace the
// placeholder below with the batch as a JSON string (paragraphs separated by "\n\n").
// Keyboard paste and textarea.value do not work on this editor; a synthetic paste does.
window.__T = "REPLACE_WITH_JSON_STRING_CONTENT";
const editor = document.querySelector('.ProseMirror');
editor.focus();
const data = new DataTransfer();
data.setData('text/plain', window.__T);
editor.dispatchEvent(new ClipboardEvent('paste', { clipboardData: data, bubbles: true, cancelable: true }));
await new Promise(resolve => setTimeout(resolve, 800));
({
  paragraphs: editor.querySelectorAll('p').length,
  counter: (document.body.innerText.match(/\d[\d,]*\s*\/\s*2,500/) || [''])[0],
  starts: editor.innerText.slice(0, 50),
})
