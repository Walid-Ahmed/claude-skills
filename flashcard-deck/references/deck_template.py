"""A deck file: copy this, then replace the topics and cards.

Render it with:
    python <skill-dir>/scripts/build_deck.py deck.py --out flashcards
The build scripts make `from flashcards import ...` work, so this file needs no path setup.
"""
from flashcards import (  # noqa: F401  (all helpers, so they are at hand while writing cards)
    a, card, code, deck, example, msg, n, pair, row, rows, topic, url,
)

DECK = deck(
    title="Git",  # shown on every card: "GIT · BRANCHES"
    credit="",    # optional README line, such as where the examples come from
    topics=[
        topic("Basics", hook="Commit · Staging · Log", cards=[
            card("staging-area", "Why does Git have a staging area?",
                 body="""
<p class="lead">It lets you choose exactly what goes into the next commit. You stage some changes, leave others, and commit only what belongs together.</p>
""" + row(n("Working folder", "files you edit", "dash"), a("git add"),
          n("Staging area", "the next commit, being built"), a("git commit"),
          n("History", "a saved snapshot", "good")) + """
<div class="boxes three">
  <div class="box"><h2>Stage</h2><p><code>git add file</code> copies the file's current state into the next commit.</p></div>
  <div class="box"><h2>Leave out</h2><p>Changes you do not add stay in your folder, ready for a later commit.</p></div>
  <div class="box"><h2>Check</h2><p><code>git status</code> lists what is staged and what is not.</p></div>
</div>
""" + example("Example: two commits from one session of edits", """
git add login.py          # only the login fix
git commit -m "Fix login redirect"
git add README.md
git commit -m "Document the setup steps"
""", lang="bash"),
                 footer="Add chooses. Commit saves.", tag="Staging"),

            card("commit-message", "What makes a good commit message?",
                 body="""
<p class="lead">A short first line that says what the commit does, in the imperative, then a blank line and the reason if it is not obvious.</p>
<table>
  <tr><th></th><th>Weak</th><th>Clear</th></tr>
  <tr><td>First line</td><td>fixed stuff</td><td>Fix login redirect after logout</td></tr>
  <tr><td>Length</td><td>A paragraph on one line</td><td>About 50 characters, then a blank line</td></tr>
  <tr><td>Body</td><td>What changed, line by line</td><td>Why it changed</td></tr>
</table>
<div class="remember"><b>To remember:</b> the diff already shows what changed. The message explains why.</div>
""", footer="Imperative first line. Why in the body.", tag="Commits"),
        ]),

        topic("Branches", hook="Branch · Merge · Rebase", cards=[
            card("what-is-a-branch", "What is a branch in Git?",
                 body="""
<p class="lead">A movable name that points at one commit. A new commit on a branch moves its name forward. Creating a branch copies nothing.</p>
<div class="steps">
  <div class="step"><span class="dot">1</span><h2>Create<span class="kind dir">Cheap</span></h2><p><code>git switch -c feature</code> adds a new name at the current commit.</p></div>
  <div class="step"><span class="dot">2</span><h2>Commit<span class="kind dir">Moves</span></h2><p>Each commit on <code>feature</code> moves only that name forward.</p></div>
</div>
""", footer="A branch is a name, not a copy.", tag="Branches"),

            card("merge-vs-rebase", "How is merge different from rebase?",
                 body="""
<p class="lead">Both bring changes from one branch into another. Merge keeps the history as it happened. Rebase rewrites your commits so they sit after the other branch's.</p>
<div class="boxes two">
  <div class="box"><h2>Merge</h2><p>Adds a merge commit with two parents. Safe on shared branches, because no commit changes.</p></div>
  <div class="box"><h2>Rebase</h2><p>Replays your commits as new ones. Gives a straight line, but never rebase commits others already pulled.</p></div>
</div>
""" + example("Example: update a feature branch with main", """
git switch feature
git merge main      # keeps history, adds a merge commit
# or
git rebase main     # rewrites feature's commits on top of main
""", lang="bash"),
                 footer="Merge preserves history. Rebase rewrites it.", tag="Merging"),
        ]),
    ],
)
