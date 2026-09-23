# Working in this repo

## The actual point of all of this

Every skill here exists to make a Commander deck **better** — not to
produce a report. "Better" means, concretely:

- **More consistent** — the deck reliably does what it's supposed to do,
  turn after turn, game after game.
- **Clear win conditions** — the deck's plan for actually winning is
  identifiable, not implied.
- **Clear lines to those win conditions** — it's not enough for a win con
  to exist; the deck needs real, findable paths to assembling it (ramp to
  get there, protection to hold the board, draw to find the pieces).
- **Efficient** — mana cost versus what a card actually does versus how
  much closer it moves the deck to a win condition. A card that's
  individually fine but doesn't pull its weight relative to what else is
  available at that cost/slot is a legitimate target for cutting, even if
  nothing about it is "wrong."

Every skill invocation — a review, a weakest-card search, a combo check, an
upgrade proposal — should ultimately serve one of these. If an interaction
with a skill doesn't move the needle on any of them, that's worth noticing.

## This repo is meant to be self-learning

Deck artifacts under `skills/review-commander-deck/decks/` are
**deliberately committed, not gitignored**. That's not just a data-hygiene
choice — those artifacts are a growing corpus of examples that sets the
quality bar for every future run. A new deck's review should be **at least
as deep** as the most thorough existing one, not shallower because this is
"just" a quick check.

More importantly: **if a skill's deterministic tooling has a gap, fix the
tooling, not just the one report it affected.** If you're reviewing a
deck and notice you had to reason your way around something by hand
because a regex, a scoring rule, or a reference doc didn't catch it — that
is the signal to go improve `analyze_deck.py`, `find_weak_cards.py`,
`find_upgrade_candidates.py`, or whichever script fell short, in the same
session, before finishing the report. Don't just note the gap and move on;
close it.

Concrete example of exactly this pattern, already established this
session: reviewing a real deck surfaced that `analyze_deck.py`'s ramp
regex didn't recognize modern templating ("add two mana in any combination
of colors") and that fetchlands were being lumped in with true tutors in
the saturation check. Both got fixed in the scripts themselves, verified
against the deck that surfaced them, and committed alongside that deck's
report — not just mentioned as a caveat in the one review. That's the
expected workflow, every time, not a one-off cleanup pass.

A currently-open example of a gap worth watching for: the instant/sorcery
side of `analyze_deck.py`'s categories is thin — there's no real detection
for things like burn spells or cantrips specifically. If a deck that leans
heavily on either of those comes through for review, that's the moment to
build that detection out, not to just describe it in prose for that one
deck.

### The loop, concretely

1. Notice the gap (something you had to reason about manually that a
   script should have caught).
2. Fix it in the actual script/regex/reference file — not a workaround in
   the report.
3. Re-verify against the deck that surfaced it.
4. If the change touches shared tooling (`analyze_deck.py`, category
   targets, scoring logic), spot-check whether it changes results for
   other already-committed decks. A result changing is fine — it should be
   an improvement — but say so plainly rather than letting history go
   silently stale.
5. Commit the tooling fix and the report together, with a commit message
   that says what gap was found and how it was closed. The git history
   here is itself part of the self-learning record — it should be
   possible to look back through it and see the tooling actually getting
   better over time, not just decks accumulating.

## Conventions already established — don't relitigate these without a reason

- **Zero third-party Python dependencies.** Every script uses only the
  standard library (`urllib`, `math.comb` instead of `scipy`, etc.), so
  any skill here works the moment it's installed, with no `pip install`
  step.
- **No shared code directory between skills.** Skills are meant to be
  individually installable (someone may copy just one skill's folder
  out). Small clients get duplicated per-skill rather than factored into a
  shared module. Deck *data* is the one thing that's intentionally shared,
  via `skills/review-commander-deck/decks/<slug>/` — see each skill's
  SKILL.md for its actual dependency graph.
- **EDHREC: never automate direct access to it.** Their Terms of Service
  explicitly bar automated queries against the site, full stop — this
  applies equally to a raw API hit and to fetching a rendered page, since
  both are "automated... requests... to the Site," not manual browsing.
  Where EDHREC-*derived* signal is genuinely useful, prefer Scryfall's own
  `edhrec_rank` field (which Scryfall computes and publishes itself,
  through their own compliant API) over touching edhrec.com. If real
  commander-specific EDHREC synergy data would help, the only acceptable
  path is asking the user to check it themselves in their browser and
  paste it in.
- **Scripts compute signals; Claude (or whoever's running the skill)
  makes the judgment call.** None of the Python here claims to fully
  "know" whether a card is good — it computes checkable facts (category
  membership, curve fit, legality, combo completion, hypergeometric
  probability) and flags them. Reading a candidate's actual oracle text
  before recommending it, every time, is not optional.
- **Verify before asserting, especially on rules questions.** This
  project has been burned twice by stating a Magic rules interaction with
  confidence instead of checking it (a blink interaction, an "Annie Joins
  Up doubles a capped trigger" question) — both times, checking the actual
  ruling either overturned or confirmed the assumption, and it mattered.
  If a claim is checkable (a card's real text, a rules interaction, an
  external API's actual behavior, a cited statistic), check it before
  it goes in a report.
- **Test against a real deck before trusting new or changed logic.**
  Every script in this repo was debugged against the actual dinos example
  deck, not just read for correctness — that's how the false positives
  and gaps above were actually found. New scoring logic, new regex
  categories, and changes to shared tooling should get the same treatment
  before being trusted.
