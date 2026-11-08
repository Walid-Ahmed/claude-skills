# Card building blocks

A card's `body` is HTML made from the blocks below. Each block already has print-friendly styling (white, coloured outlines, the topic's colour) in `scripts/flashcards/card.css`, so use the class names as shown and add no inline colours.

The card is 1200 x 849 CSS px. After the header and question, the answer has roughly 560 px of height. A lead plus one row of boxes plus a 6 to 10 line example is a typical full card. `build_deck.py` reports how much space each card has left ("spare") or how much it overflows.

## Contents

- Text: lead, section label, inline code, remember callout
- Boxes: two, three, or four in a row; kicker; highlighted box; definition list
- Steps: numbered steps with tags
- Tables: plain table, step table with code cells
- Code: example(), pair(), request/response panels
- Special: formula row, JSON boxes, coloured token, good/bad tags
- Diagrams: row, labelled rows, URL parts, labelled message

## Text

```html
<p class="lead">One or two sentences that answer the question on their own.</p>
<div class="section">A small capital label for what follows</div>
<code>inline_code()</code>   <!-- a chip: it never wraps, so keep it short, and leave a space or punctuation after it -->
<div class="remember"><b>To remember:</b> one memorable rule, a contrast, or a common mistake.</div>
```

Start every body with a `lead`. Diagrams in this skill sit right after it. Use `remember` once per card at most. Its bold label can be anything short: "To remember:", "Why:", "Do not mix these up:", "Order matters:".

## Boxes

```html
<div class="boxes three">   <!-- or "boxes two", "boxes four" (four needs class "four" on the same div) -->
  <div class="box"><h2>Save</h2><p>Short explanation, one or two sentences.</p></div>
  <div class="box"><div class="kicker">Library</div><h2>SQLAlchemy</h2><p>...</p></div>
  <div class="box hot"><h2>The odd one out</h2><p>Thicker outline, to single one box out.</p></div>
</div>

<div class="box"><h2>Authentication</h2>
  <dl><dt>Question</dt><dd>Who are you?</dd><dt>Failure</dt><dd><code>401</code></dd></dl>
</div>
```

Three boxes is the usual pattern for "three parts" or "three facts". Each box should be 1 to 3 short lines; longer text belongs in fewer, wider boxes.

## Steps

```html
<div class="steps">          <!-- two per row; add "three" or "four" for more per row -->
  <div class="step"><span class="dot">1</span><h2>Log in<span class="kind dir">Client → server</span></h2>
    <p>What happens in this step, in one or two sentences.</p></div>
  <div class="step"><span class="dot">2</span><h2>Check<span class="kind authn">Authentication</span></h2><p>...</p></div>
</div>
```

The tag inside `h2` is optional. Tag styles: `kind dir` (neutral, for directions such as "Client → server"), `kind authn` (indigo), `kind authz` (green), `kind setup` (dashed). For "four", keep each step to about 20 words.

## Tables

```html
<table>
  <tr><th></th><th>Request model</th><th>response_model</th></tr>
  <tr><td>Checks</td><td>Data coming in</td><td>Data going out</td></tr>
  <tr><td>Failure</td><td><code>422</code></td><td><code>500</code></td></tr>
</table>
```

The first column is bold automatically. For a row-by-row walkthrough with code, use the step table, where `mono` puts a line of code on its own line inside a cell:

```html
<table class="flow-table">
  <tr><th>Step</th><th>What travels</th><th>Code that handles it</th></tr>
  <tr><td>1 · Log in<span class="kind dir">Client → server</span></td>
      <td><code>POST /auth/token</code> with form fields:<span class="mono">username=alice&amp;password=...</span></td>
      <td><span class="mono">verify(password, user.hashed_password)</span>A wrong password stops here with <code>401</code>.</td></tr>
</table>
```

## Code

Use the Python helpers in `deck.py` rather than writing `<pre>` by hand. They escape and colour the code.

```python
example("Example: books.py", """
@app.get("/books/{book_id}")
async def read_book(book_id: int):
    ...
""")                     # lang="python" by default; also bash, json, js, sql, dockerfile, yaml, toml, text

pair(example("Before", old_code), example("After", new_code))   # two code boxes side by side

code("SELECT * FROM users;", lang="sql")   # just the coloured code, to place in your own <pre>
```

Keep examples to about 6 to 12 lines. Cut with `...` rather than letting a card overflow. Comments inside examples explain why, not what.

Two panels side by side, such as a request and its response, with a note under one:

```html
<div class="reqs">
  <div class="snippet req"><div class="cap">Example: the request</div><pre>GET /todo/1 HTTP/1.1
<b>Authorization: Bearer eyJhbGci...</b></pre></div>
  <div class="snippet req"><div class="cap">Example: the reply</div><pre>{"id": 1, "title": "Buy milk"}</pre>
    <p class="note">A short note under the code.</p></div>
</div>
```

Inside a hand-written `<pre>`, escape `<`, `>`, and `&` as `&lt;`, `&gt;`, `&amp;`. In a Python string, write a backslash as `\\`.

## Special blocks

```html
<div class="formula">                 <!-- input + input → output -->
  <div class="part"><span class="label">Input 1 · The message</span>header + payload</div><div class="sign">+</div>
  <div class="part"><span class="label">Input 2 · The key</span>the secret key</div><div class="sign">→</div>
  <div class="part"><span class="label">Output</span>the signature</div>
</div>

<div class="boxes three"><div class="jsonbox"><h2>1. Header</h2><p>How it is signed.</p><pre>{ "alg": "HS256" }</pre></div>...</div>

<div class="tok"><span class="a">eyJhbGci</span>.<span class="b">eyJzdWIi</span>.<span class="d">BO0CINuy</span></div>   <!-- coloured parts of one string -->

<div class="cap">Before <span class="tag-bad">No validation</span></div>   <!-- or tag-good -->
```

## Diagrams

Python helpers that return HTML. Put the diagram right after the lead: `body = '<p class="lead">...</p>' + row(...) + '...'`.

```python
row(n("Request", "GET /", "dash"), a(),
    n("Route decorator", "matches method and path"), a("runs"),
    n("Your function", fail="Raises: 404"), a("returns"),
    n("Response", "200, JSON", "good"))
```

- `n(title, sub="", kind="", fail="")` is a box. `kind` is `"dash"` (data or the client), `"good"` (green, a success), `"bad"` (red, a failure), or empty. `fail` adds red outcome lines, as a string or a list.
- `n()` takes HTML: wrap commands and code in `<code>` (in a bold title, `COPY . .` reads as `COPY ..` without it), and escape `<`, `>`, `&` yourself. `url()` and `msg()` take plain text and escape it for you.
- `a(label="", left=False)` is an arrow with an optional small label in code font. `left=True` points back to the previous box, which suits two sides meeting in the middle (A → result ← B). For a request and its reply, use two labelled rows (`rows()`) rather than mixing directions in one row. The arrow widens to fit its label, which takes width from the boxes, so keep labels short: a command or two words, about 14 characters at most.
- Four boxes in a row is comfortable; five is the most.

Labelled rows line up in columns, for comparing paths. The labels sit on the left. A shorter row is padded with invisible boxes so its columns match the longest row, and every arrow has the same width, so arrow labels in `rows()` should stay under about 10 characters:

```python
rows(("Ctrl+C", [n("Running"), a("Ctrl+C"), n("Stopped", "port free", "good")]),
     ("Ctrl+Z", [n("Running"), a("Ctrl+Z"), n("Paused", "port busy", "bad"), a("fg"), n("Stopped", "", "good")]))
```

A URL or command split into labelled parts:

```python
url(("/books/", ""), ("1", "Path value<br>before the ?"), ("?", ""), ("rating=5", "Query value<br>after the ?"))
```

A message with each part labelled:

```python
msg(("POST /books HTTP/1.1", "Method and URL"),
    ("Content-Type: application/json", "Headers"),
    ('{"title": "Dune"}', "Body"))
```

## Deck-wide style tweaks

`deck(..., extra_css="...")` adds CSS to every card in the deck, for a rare tweak such as `.box p { font-size: 13px; }`. Prefer the blocks as they are: if a layout needs a tweak, it may belong in a different block.

A diagram costs 70 to 170 px of height, so it fits on cards with room to spare. If a card overflows after adding one, the diagram is probably repeating what the text says. Drop one of them.
