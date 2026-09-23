---
name: find-deck-combos
description: Checks an already-reviewed Commander deck against Commander Spellbook's combo database - what infinite/game-winning combos the deck already has, and what combos it's one or two cards away from. Use when the user asks if their deck has any combos, why a specific card is in the deck, or before recommending any card as a cut (a "weak" card can be a load-bearing combo piece).
---

# Find Deck Combos

Cross-references a deck's card pool against [Commander Spellbook](https://commanderspellbook.com),
the community combo database, via its public API. Two purposes: surface
combos already sitting in the decklist (sometimes unintentionally - a card
that looks narrow/weak in isolation can turn out to be a combo piece), and
find near-miss combos the deck could complete with one or two more cards.

## Requires review-commander-deck to have already run on this deck

Reads `context.json` from `../review-commander-deck/decks/<slug>/`. Run
that skill's pipeline first if it doesn't exist yet for this deck.
`review-commander-deck` now runs this skill itself as part of its own
workflow when it's installed alongside it, so `combos.json` may already
exist and be current — check before re-running. Re-run it if the decklist
has changed since `combos.json`'s timestamp, or if it's missing entirely
(e.g. `review-commander-deck` was run without this skill installed).

## Why Commander Spellbook and not EDHREC

Commander Spellbook is open source (MIT license) and its API is built for
exactly this kind of programmatic use - documented OpenAPI schema, a
published npm client, no authentication required for combo lookups, and a
stated rate-limit guideline (80 req/min) rather than a prohibition. This is
a different situation from EDHREC, whose Terms of Service explicitly
forbid automated queries (see `find-weakest-cards`'s SKILL.md) - that
distinction is why this integration exists and the EDHREC one doesn't.

## Workflow

1. **Run the lookup** from this skill's root:
   ```
   python3 scripts/find_combos.py --deck-dir ../review-commander-deck/decks/<slug>
   ```
   Writes `../review-commander-deck/decks/<slug>/combos.json` with two lists:
   - `included` — every piece is already in the deck. Read every one of
     these; if the user didn't already know about it, this is often the
     most useful thing you tell them.
   - `almost_included` — missing one or more cards (see each entry's
     `missing_cards`). This list is typically large (dozens of entries) and
     includes plenty of noise (combos that happen to share one incidental
     card with the deck). Sort by `len(missing_cards)` ascending, then by
     `popularity` descending, and only surface the handful that are
     actually one card away and reasonably well-known - don't dump the
     whole list on the user.

2. **Read each combo's `notes`, `produces`, `easy_prerequisites`, and
   `notable_prerequisites`** before describing it. `produces` is a list of
   short feature names (e.g. "Infinite creature tokens," "Draw the game")
   - some are *not* wins by themselves (a forced draw is bad for you unless
     something else converts it). Don't call something a win condition
     without checking whether its `produces` list is actually favorable.

   **This is not optional, and skipping it has already caused a real
   mistake in this project.** A combo's `cards` list is "every card this
   needs to be in the 99" - it is *not* "everything that needs to be true
   for this to actually loop." `Raptor Hatchling` + `Warstorm Surge` was
   presented as a clean combo completion by only checking that both cards
   existed; the variant's actual `notablePrerequisites` read "You have a
   way to give Raptor Hatchling indestructible" - without that (a fourth
   thing, not itself a listed card), a 1-toughness creature dies to the
   first instance of the very damage that triggers it, and the "loop" is
   one activation. The general pattern: a creature with a "whenever this
   creature is dealt damage" trigger needs toughness that can survive
   whatever's dealing that damage, repeatedly, or it needs external
   protection - check the creature's own `toughness` in `context.json`
   against what's actually going to hit it, every time, not just when a
   prerequisite happens to be listed. `review-commander-deck`'s
   `fragile_trigger` category (toughness ≤2 with this exact trigger
   shape) catches the narrow, clearly-fragile case automatically; it
   won't catch every version of this (e.g. `Forerunner of the Empire` is
   a 1/3 that dies to *accumulated* damage over several loop iterations,
   not the first hit) - read the actual numbers, don't assume the
   automated flag caught everything.

3. **The database models loops, not every community-known finishing touch.**
   A combo that loops forever but only "draws the game" per Commander
   Spellbook's data might still be a real win in practice if the deck has
   another card that redirects the loop's damage/effect favorably - that
   specific combination may not exist as its own cataloged variant. Check
   the deck's other cards by hand (read their `oracle_text` in
   `context.json`) for anything that would turn a "draw" loop into a win,
   the same way you'd verify any other heuristic-flagged signal in this
   skill set. Say plainly when you're doing this inference vs. quoting the
   database directly.

## Cross-check before calling anything "weak"

If `find-weakest-cards` is also being used on this deck, run this skill
**first** (or check if `combos.json` already exists) and cross-reference
its `included` list before recommending any card as a cut. A card that
looks narrow or conditional in isolation can be exactly the piece that
makes an infinite combo work — narrow-looking text is often what a combo
piece looks like from the outside.

## Known limitations

- Only checks the card pool, not deck order/mana - a combo being "included"
  doesn't mean it's easy to assemble in a real game, just that every card
  it needs is somewhere in the 99. It also doesn't mean the loop actually
  sustains itself once assembled - see step 2 above.
- `almost_included` can be large and noisy; use judgment on what's worth
  surfacing rather than reporting everything the API returns.
- `find_combo_completions.py` (in `upgrade-commander-deck`) now surfaces
  `free_combo_count` alongside raw `combo_count` for exactly this reason -
  a completion with no listed prerequisites is a more reliable signal than
  one that technically completes more combos but needs extra setup for
  all of them. Still read the actual `prerequisites` field before
  recommending anything; the count alone doesn't tell you whether the
  prerequisite is trivial (a creature with power 4+, easy in most decks)
  or a real ask (a whole extra card slot dedicated to protection).
