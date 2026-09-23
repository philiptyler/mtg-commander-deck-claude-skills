---
name: upgrade-commander-lands
description: Optimizes the mana base (lands only) of an already-reviewed Commander deck using a computed hypergeometric probability model, not raw intuition, to find real color-fixing shortfalls, then proposes N land swaps. Use when the user asks to fix, optimize, or upgrade the mana base of a deck already run through review-commander-deck. Never proposes nonland swaps - that's upgrade-commander-deck's job.
---

# Upgrade Commander Lands

Finds real mana base shortfalls with an actual computed probability, not a
lookup table or a hunch, then proposes N land swaps to fix the worst ones.
Scope boundary: **lands only** — if the math says the deck actually needs
more ramp/fixing spells rather than more lands, say so and point at
`upgrade-commander-deck`, don't make that swap here.

## Requires review-commander-deck to have already run on this deck

Reads `context.json` from `../review-commander-deck/decks/<slug>/`.
Applying a confirmed proposal delegates to `update-commander-deck`, same as
`upgrade-commander-deck`.

## The math, and why it's computed rather than looked up

A commonly-cited Frank Karsten figure for a 99-card Commander deck is
"~22 sources for reliable single-pip casting, ~29 for double-pip" — but a
reliable turn-by-turn breakdown specific to Commander wasn't verifiable
from primary sources when this skill was built (checked before writing
anything down; see `scripts/hypergeometric.py`'s docstring for what was and
wasn't confirmed). Rather than repeat a table this project couldn't check,
`mana_base_analysis.py` computes the actual probability directly from the
deck's real current source counts using the hypergeometric distribution
(stdlib `math.comb`, no scipy) — sanity-checked against those
externally-corroborated 22/29-source figures and it lines up. Read that
script's docstring before changing the model.

Sources come from every card's `produced_mana` field (lands *and* mana
rocks/dorks both count) — not from `analyze_deck.py`'s `ramp` category,
which is about mana acceleration broadly and isn't the same thing as
"produces this specific color."

## Workflow

1. **Parse the request:** how many swaps (N), and any stated concern
   (color screw, a specific double-pip card not coming down on time).

2. **Run the model:**
   ```
   python3 scripts/mana_base_analysis.py --deck-dir ../review-commander-deck/decks/<slug>
   ```
   Writes `mana_base_analysis.json`. If `mono_or_colorless` is true, say so
   plainly and stop the color-fixing analysis — focus any land swaps on
   utility (recursion, card advantage, a win condition) instead, since
   there's no fixing problem to solve. Otherwise read `tier_results`: each
   entry is one (curve tier, color) combination with `current_sources`,
   the computed `probability`, and `status` (`OK`/`SHORTFALL` against the
   ~90% target in `hypergeometric.TARGET_PROBABILITY`). `at_risk_cards`
   names the actual double/triple-pip cards a shortfall puts at risk —
   lead with those, not the raw percentage; "this puts `Grand Abolisher`
   (`{W}{W}`) at real risk of not being live by turn 2" is a lot more
   useful than "65%."

3. **Pick the N worst shortfalls** (lowest probability relative to target,
   weighted toward earlier tiers — a turn-2 shortfall matters more than a
   turn-5+ one) to address. If the user named a specific concern, prioritize
   that color/tier even if it isn't the mathematically worst one, but
   mention the worse one too.

4. **Source land candidates for each shortfall color:**
   ```
   python3 scripts/find_land_candidates.py --deck-dir ../review-commander-deck/decks/<slug> \
       --color <W|U|B|R|G> --count 10 [--budget <usd>] [--prefer-untapped]
   ```
   Pass `--prefer-untapped` for tier 1-2 shortfalls specifically — an
   always-enters-tapped land is a real cost exactly when the deck needs
   that color online early; it matters less for a tier 5+ shortfall. Read
   `enters_tapped_no_upside` per candidate, but verify against the card's
   own `oracle_text` before trusting it — it's the same kind of regex
   heuristic `find-weakest-cards` already documented as capable of missing
   real upside phrased unusually.

5. **Pick which basic to cut** for each swap: favor cutting a basic in
   whichever color is *most over-served* relative to its own pip demand
   (check the other colors' `tier_results` — don't cut into a color that's
   already a shortfall itself).

6. **Present the proposal and wait for confirmation** — same as
   `upgrade-commander-deck`, nothing applies automatically. Show each swap
   with the math: current probability, and what it becomes.

7. **On confirmation, apply via `update-commander-deck`** (same pattern as
   `upgrade-commander-deck` step 6: snapshot, edit `decklist.txt`, re-run
   the pipeline, diff). Then **re-run `mana_base_analysis.py`** and show
   the before/after probability for each color you touched — don't just
   assert the swap helped, show the recomputed number.

## Known limitations

- Hybrid and Phyrexian mana symbols (e.g. `{G/U}`, `{G/P}`) are excluded
  from pip counting entirely (see `hypergeometric.py`/`mana_base_analysis.py`
  docstrings) — they're strictly easier to cast than a dedicated pip since
  either half satisfies them, and modeling that properly needs joint
  probability across combinations. This means a deck leaning heavily on
  hybrid costs will look like it needs less fixing than a literal reading
  of its mana costs might suggest, which is directionally correct, just
  not precisely modeled.
- The turn-2/4/5 tier boundaries are a simplification (real curves are
  continuous); a card at exactly CMC 2 or CMC 4 is bucketed at the tier
  boundary, which is usually the conservative (more demanding) choice but
  worth knowing about for an edge case.
- Assumes "on the play" (no turn-1 draw) — this is the stricter assumption;
  the real numbers on the draw are slightly better than what's reported.
