---
name: update-commander-deck
description: Applies card swaps/additions/cuts to a deck already reviewed by review-commander-deck and refreshes every downstream artifact (context, analysis, combos, report), reporting exactly what changed. Use when the user has already had a deck reviewed and now wants to swap, add, or cut specific cards - not for a first-time review of a new decklist.
---

# Update Commander Deck

Takes a small set of card changes to an already-reviewed deck, applies them
to `decklist.txt`, re-runs the pipeline, and reports **what actually
changed** as a result — not just "here's the new report," but "ramp went
from 12 to 11, the bracket estimate didn't move, and this swap broke the
Polyraptor combo." That last kind of finding is the entire point of this
skill; regenerating the artifacts is the easy part.

## Requires review-commander-deck to have already run on this deck

Everything here re-runs `review-commander-deck`'s own scripts (and
`find-deck-combos`'s, if installed) rather than duplicating them — this
skill only adds the diff step. If the deck hasn't been reviewed yet, use
`review-commander-deck` first; this skill is for changing an existing deck,
not reviewing a new one.

## Workflow

1. **Confirm the exact change** before touching anything: which card(s) are
   coming out, which are going in, and quantities. Read it back to the user
   if there's any ambiguity (e.g. "swap the raptor" when the deck has three
   raptor cards) — don't guess which card they mean.

   This includes confirming *that a change should happen at all*, not just
   which cards. If this skill is being invoked to apply a swap
   `upgrade-commander-deck` proposed earlier, make sure the user actually
   said to apply it — "that's a better suggestion" or "I like this
   direction" is approval of the *analysis*, not authorization to execute.
   This confusion has already caused a real mistake in this project: a
   swap got applied from exactly that kind of warm-but-not-explicit
   response, and had to be reverted. If it's not unambiguous, ask.

2. **Snapshot the current state** (from this skill's root):
   ```
   python3 scripts/snapshot_before.py --deck-dir ../review-commander-deck/decks/<slug>
   ```
   Do this *before* editing the decklist — the diff step needs a baseline.

3. **Edit `../review-commander-deck/decks/<slug>/decklist.txt` directly**
   (it's a plain text file — use your normal file-editing tools). Remove the
   outgoing card's line entirely, or decrement its quantity if it's a
   multi-copy line (basic lands). Add the incoming card as a new line —
   plain `1 Card Name` is fine, it doesn't need to match whatever tagged
   format the rest of the file uses. If the commander itself is changing,
   say so explicitly to the user before proceeding — that changes the
   deck's whole color identity, which step 6 below checks for fallout.

4. **Re-run the core pipeline** from `../review-commander-deck`:
   ```
   python3 scripts/fetch_cards.py --deck-dir decks/<slug>
   python3 scripts/build_context.py --deck-dir decks/<slug>
   python3 scripts/analyze_deck.py --deck-dir decks/<slug>
   ```
   The Scryfall cache means only genuinely new cards get fetched — this is
   fast for a small swap, not a full re-review.

5. **Re-run whichever of these were already in use for this deck** (check
   whether their output files already existed before this update):
   ```
   python3 ../find-deck-combos/scripts/find_combos.py --deck-dir ../review-commander-deck/decks/<slug>
   python3 ../find-weakest-cards/scripts/find_weak_cards.py --deck-dir ../review-commander-deck/decks/<slug>
   ```
   Skip either one gracefully if that skill isn't installed.

6. **Diff:**
   ```
   python3 scripts/diff_after.py --deck-dir ../review-commander-deck/decks/<slug>
   ```
   Writes `../review-commander-deck/decks/<slug>/last_update_diff.json`.
   The `.update-tmp` snapshot is deliberately left in place (not
   auto-deleted) — safe to re-run this diff step again against the same
   baseline if you need to (e.g. you found and fixed a tooling bug
   mid-update and need to re-run `analyze_deck.py` before re-diffing).
   `snapshot_before.py` is what refreshes it, the next time it's explicitly
   run for a new update cycle. Read the diff and lead with what matters
   most, in this order:
   - `combos_lost` — **this is the headline if it's non-empty.** A swap that
     silently breaks a combo is exactly the kind of thing a mechanical
     "regenerate the report" pass would miss. Say plainly which combo broke
     and why (which removed card it needed).
   - `card_count_warning` — deck isn't 100 cards anymore, flag it.
   - `violations` (color identity) — only relevant if the commander changed
     or a card was added that's outside its identity; Scryfall legality
     data doesn't catch this on its own, this check does.
   - `bracket_before` / `bracket_after` — if it moved, say why (read the new
     `analysis.json`'s `bracket_estimate.reasoning`).
   - `category_changes` / `counts_delta` — the ordinary "here's what shifted"
     summary.
   - `curve_delta` — real computed curve movement, both nominal and
     effective-CMC-adjusted (`typical_*` — see
     `review-commander-deck/references/effective_cmc.md`), plus
     `baseline_reference` (a cited community band, not a pass/fail rule —
     see that same file for why). Use this instead of eyeballing "CMC 4 →
     CMC 2 must be an improvement" — added after direct feedback that
     swaps were being justified on curve with no actual tooling behind the
     claim.
   - `combos_gained` — worth celebrating if the swap happened to create one.

7. **Update `report.md`.** For a small change with a small diff, a short
   "Updated `<date>`: swapped X for Y — Z changed as a result" note is
   enough; don't rewrite the whole document for a one-card swap. For a
   change that moved the bracket estimate, gained/lost a combo, or shifted
   a category from "within" to "over"/"under" its target range, update the
   relevant prose section too so the report doesn't go stale and
   contradict itself.

## Known limitations

- This applies changes you already decided on — it doesn't suggest which
  cards to swap. (A future `optimize-commander-deck` skill, not built yet,
  would be the one that recommends changes; this one just applies them
  and reports the impact.)
- The color identity check only looks at nonland cards' `color_identity`
  field against the commander's; it won't catch a nonbasic land that's
  fine to include but doesn't produce a color the deck needs (that's
  `find-weakest-cards`'s `off_color` signal, not this skill's job).
