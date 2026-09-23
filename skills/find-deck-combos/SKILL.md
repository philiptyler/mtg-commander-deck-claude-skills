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
  it needs is somewhere in the 99.
- `almost_included` can be large and noisy; use judgment on what's worth
  surfacing rather than reporting everything the API returns.
