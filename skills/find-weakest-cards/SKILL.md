---
name: find-weakest-cards
description: Finds the weakest N cards in an already-reviewed Commander decklist, optionally scoped to a specific slice (lands, removal, ramp, card draw, tutors, or all nonland cards). Use when the user asks things like "what are the weakest 3 cards in my deck," "what are the weakest 2 lands," or "what's the worst removal spell here" for a deck already run through review-commander-deck.
---

# Find Weakest Cards

Surfaces cut candidates from an already-reviewed deck by combining computed
signals (category oversaturation, cards with no detected functional role,
high-CMC single-purpose cards, land quality issues) with your own reading
of each candidate's actual card text — the script gives you signals, not a
verdict.

## Requires review-commander-deck to have already run on this deck

This skill reads `context.json` and `analysis.json` from
`../review-commander-deck/decks/<slug>/`. If those don't exist yet for the
deck in question, run `review-commander-deck`'s pipeline first (or at least
its `fetch_cards.py` → `build_context.py` → `analyze_deck.py` steps) —
don't re-implement decklist parsing or Scryfall fetching here.

## Workflow

1. **Figure out the deck and the ask.** You need: which deck (its slug
   under `review-commander-deck/decks/`), how many cards (N — if the user
   doesn't say, ask; don't assume 1), and the scope:
   - "weakest N cards" / "weakest N nonland cards" → all nonland, non-commander cards
   - "weakest N lands" → lands only
   - "weakest N removal spells" / "weakest N ramp" / etc. → that specific
     category from `analysis.json`'s `categories` (map their wording to the
     closest category key: removal → `targeted_removal` + `board_wipe`,
     ramp → `ramp`, draw → `card_draw`, tutors → `land_tutor` +
     `nonland_tutor`)
   - Also ask what they're optimizing for if it's not obvious ("weakest against
     what?" — e.g. "weakest at closing games fast" vs. "weakest for
     Bracket 3 in general" can point at different cards).

2. **Run the signal script** from this skill's root:
   ```
   python3 scripts/find_weak_cards.py --deck-dir ../review-commander-deck/decks/<slug>
   ```
   Writes `../review-commander-deck/decks/<slug>/weak_card_signals.json`.
   Re-run it if `analysis.json` has changed since the last run (e.g. after
   a decklist edit); otherwise the existing file is fine to reuse across
   multiple questions about the same deck.

3. **Read `weak_card_signals.json` alongside `context.json`.** It has four
   parts:
   - `category_saturation` — actual count vs. bracket-scaled target range
     per category (see `references/category_targets.md`), status
     under/within/over. "Over" categories are where individual weak members
     are most cuttable — the deck doesn't need all of them.
   - `roleless_nonland_cards` — nonland cards matching none of
     `analyze_deck.py`'s categories. **Not automatically weak** — plenty of
     good cards (efficient beaters, tribal payoffs, combo pieces) won't hit
     any text-based category. Use this as one input, not a verdict.
   - `high_cmc_low_role_cards` — CMC 6+ cards matching zero or one category.
     Expensive AND narrow is a real signal; expensive and multi-role
     (ramp + draw + win-con in one card) usually isn't a cut candidate even
     at high CMC.
   - `land_signals` — per land: `enters_tapped_no_upside_hint` (regex-only,
     **will miss real upside phrased unusually** — e.g. a land that cheats
     a creature into play instead of gaining life/scrying won't show
     upside here even though it has one) and `off_color` (produces a color
     outside the deck's color identity).
   - `fragile_trigger_cards` — the inverse of a signal, a caveat: creatures
     whose payoff needs "this creature is dealt damage," at toughness ≤2,
     where that same damage is likely to kill them too. Weigh this heavily
     if the card's whole appeal (e.g. a combo pitch from
     `find_combo_completions.py`) rests on repeated activations — a card
     that can only trigger once isn't the engine piece it looks like on
     paper. This only catches the narrow "dies to the first hit" case by
     toughness alone; a card that dies to *accumulated* damage over several
     iterations (higher toughness, but the trigger deals damage to itself
     too) won't show up here — read the actual numbers by hand for
     anything with a self-referential damage trigger, don't assume this
     list is exhaustive.

4. **Before naming a card as weak, read its actual `oracle_text` in
   `context.json`.** The signals are heuristic flags, not conclusions — a
   card flagged `enters_tapped_no_upside_hint: true` might still have real
   upside the regex didn't recognize (this happened during testing: a land
   that cheats a big creature into play got flagged, because its upside
   isn't "scry" or "gain life" or "unless," it's something else entirely).
   Don't repeat a flag as your reasoning without checking the card behind it.

5. **Check `find-deck-combos` before finalizing any candidate.** Run
   `../find-deck-combos/scripts/find_combos.py --deck-dir
   ../review-commander-deck/decks/<slug>` (or read the existing
   `combos.json` if it's already there) and check whether any candidate
   card appears in its `included` list. **Do not call a combo piece
   "weak"** — a narrow, conditional-looking card is exactly what a combo
   piece looks like from the outside. This is not a hypothetical: an
   earlier pass of this skill called `Wrathful Raptors` one of a deck's two
   weakest removal spells because it only triggers reactively; it's
   actually the payoff for an infinite-damage combo with `Polyraptor` and
   `Marauding Raptor` already in the same deck, and the deck separately has
   a second, unrelated infinite combo (`Polyraptor` + `Forerunner of the
   Empire`) that hadn't been noticed at all. Both were only caught by
   actually checking the combo database, not by reading card text harder.

6. **Answer the specific question**, ranked, with reasoning tied to *this
   deck's plan* — reference what the deck is trying to do (from the
   original review's synthesis, if you have it) rather than generic power
   level. Say why each pick is weaker than what else the deck is doing at
   a similar cost/role, not just "this card is bad."

## EDHREC data — don't automate it

EDHREC's `json.edhrec.com` endpoint has real per-card synergy/inclusion-rate
data for a given commander, but their Terms of Service explicitly prohibit
"automated searches, requests, or queries to the Site." **Do not write
scripts that fetch it.** If EDHREC context would sharpen an answer (e.g.
"this card is only in 8% of Pantlaza decks"), ask the user to check it
themselves in their browser and paste the number in — normal human
browsing, not automation — and factor it in when they do.

## Known limitations

- Category targets in `references/category_targets.md` are sourced from
  general Commander deckbuilding convention (mostly one source, the
  "Command Zone Template," for Bracket 3) extrapolated by hand for other
  brackets — treat "over"/"under" as a prompt to look closer, not a rule.
