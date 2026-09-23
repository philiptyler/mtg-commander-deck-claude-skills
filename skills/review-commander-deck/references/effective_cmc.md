# Effective CMC and curve targets

Computed by `scripts/analyze_deck.py`, consumed by `find-weakest-cards`,
`upgrade-commander-deck`, and `update-commander-deck`'s diff. This file
exists because a first version of the "weakest cards" tooling recommended
cutting `The Skullspore Nexus` — CMC 8 printed — without ever noticing its
text says *"this spell costs {X} less to cast, where X is the greatest
power among creatures you control."* In a deck built around big creatures,
its real typical cast cost was 4, sometimes free. Printed CMC was silently
standing in for "what this card actually costs to play," and for a card
with real cost reduction, those aren't the same number.

## What's genuinely deterministic here, and what isn't

Unlike `upgrade-commander-lands`'s mana-base math — a single, universally-
agreed hypergeometric model — "what should this deck's curve look like" has
**no equivalent rigorous formula** in the community. Checked directly before
building anything (same discipline as everywhere else in this project):
guidance from multiple sources (Draftsim, a geekydomain deckbuilding guide,
several forum threads) converges on a *qualitative* shape — "a modest count
at 1, a strong count at 2, the bulk at 3-4, tapering at 5-6, a small handful
of finishers at 7+" — plus two citable numeric anchors:

- **Average mana value target: 2.5-3.5.**
- **At least 50% of nonland cards at CMC 3 or less.**

Neither source offered a precise, quantitative adjustment for "how much
should more ramp/card draw/a costlier commander shift this target" — that
part stayed qualitative even in guides that stated the two numbers above
plainly. So this project doesn't invent one either. `curve_summary`'s
`baseline_reference` is exactly those two cited numbers, presented as a
**band to weigh against, not a pass/fail target** — a deck with
above-typical ramp and cost-reduction density (this repo's example deck has
both) can reasonably sit above that band without it being a real problem,
but that's a judgment call for whoever's reading the numbers, not something
the script asserts for you.

## What IS computed rigorously: effective CMC

For a card with **its own** cost reduction (not one it grants to other
cards — see below), `analyze_deck.py`'s `effective_cmc()` computes:

- **`nominal_cmc`** — printed CMC. Always the honest, guaranteed-worst-case
  number; every other signal in this repo (`curve_bucket`, `high_cmc_low_role`
  in `find-weakest-cards`, etc.) still uses this by default, on purpose —
  see "conditional cost, again" below.
- **`typical_cmc`** — for a fixed reduction ("this creature costs {1} less
  to cast"), this is exact and reliable. For a *scaling* reduction tied to
  creature power, it's `nominal - median(power of this deck's own
  creatures)` — a labeled **estimate**, not a guarantee, since board state
  varies game to game.
- **`best_case_cmc`** — same idea using this deck's *maximum* creature
  power. A ceiling, explicitly not a promise.

Both curves get reported: `mana_curve` (nominal, unchanged) and
`typical_mana_curve` (using `typical_cmc` where computed). Read both — a
card that's usually cheap but occasionally expensive is different from one
that's always in between, and only the two numbers together show that.

## Scope: self reduction only, not granted reduction

`Marauding Raptor` ("Creature spells you cast cost {1} less to cast") and
`Hunting Velociraptor` ("Dinosaur spells you cast have prowl {2}{R}") grant
a discount to *other* cards in the deck — they don't reduce their own
casting cost at all. Modeling that properly means matching each granted
discount's criteria (color, type, timing condition) against every other
card in the deck, and handling multiple stacking granters — out of scope
here. `effective_cmc()` is deliberately anchored to self-referential
phrasing ("this spell/creature costs...") and excludes the granted form
(a negative lookbehind for "have " before "warp"/"prowl", specifically
because "X spells you cast **have** prowl {cost}" is the granted-form
tell). A first version of this fix didn't have that exclusion and computed
a meaningless "best case" cost for `Hunting Velociraptor` and `Tannuk,
Steadfast Second` from a discount that was never theirs to use — caught by
checking the actual output, not by inspection.

## Conditional cost, again

`upgrade-commander-deck` already has a `conditional_discount` flag (see its
own docstring — the Ride's End lesson: a discount that depends on board
state isn't reliably cheap, and shouldn't be silently read as if it were).
`effective_cmc()`'s `typical_cmc`/`best_case_cmc` are the same category of
information, presented more precisely, with the same caveat: `typical_cmc`
is a reasonable expectation, not a floor. Prowl and warp specifically get
`typical_cmc == nominal_cmc` (no discount applied to the "typical" number
at all) precisely because their discount requires a specific game state
(combat damage already dealt, or accepting warp's end-of-turn exile) that a
"how much does this usually cost" estimate shouldn't assume — only
`best_case_cmc` reflects the alternate cost, clearly labeled as a ceiling.
